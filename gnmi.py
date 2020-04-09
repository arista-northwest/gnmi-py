#!/usr/bin/env python3
"""
Python3 CLI utility for interacting with Network Elements using gNMI.

Based on: https://github.com/google/gnxi/blob/master/gnmi_cli_py/py_gnmicli.py

Current supported gNMI features:

- Subscribe
"""
import argparse
import json
import re
import os
import sys

import grpc
import google.protobuf
from gnmi.proto import gnmi_pb2 as pb
from gnmi.proto import gnmi_pb2_grpc

__version__ = "0.1.6"

if sys.version_info < (3, 6):
    # see: https://devguide.python.org/devcycle/
    raise ValueError("Python 3.6+ is required")

_PROG_NAME = "gnmi-py"

_RE_PATH_COMPONENT = re.compile(r'''
^
(?P<pname>[^[]+)
(\[(?P<key>[a-zA-Z0-9\-\/\.]+)
=
(?P<value>.*)
\])?$
''', re.VERBOSE)


def decode_bytes(bites, encoding='utf-8'):
    # python 3.6+ does this automatically
    if sys.version_info < (3, 6):
        return bites.decode(encoding)
    return bites


def escape_string(string, escape):
    result = ""
    for character in string:
        if character in (escape, "\\"):
            result += "\\"
        result += character
    return result


def extract_value(update):

    val = None

    if not update:
        return val

    try:
        val = extract_value_v4(update.val)
    except ValueError:
        val = extract_value_v3(update.value)

    return val


def extract_value_v3(value):
    val = None
    if value.type in (pb.JSON_IETF, pb.JSON):
        val = json.loads(decode_bytes(value.value))
    elif value.type in (pb.BYTES, pb.PROTO):
        val = value.value
    elif value.type == pb.ASCII:
        val = str(value.value)
    else:
        raise ValueError("Unhandled type of value %s" % str(value))
    return val


def extract_value_v4(value):
    val = None
    if value.HasField("any_val"):
        val = value.any_val
    elif value.HasField("ascii_val"):
        val = value.ascii_val
    elif value.HasField("bool_val"):
        val = value.bool_val
    elif value.HasField("bytes_val"):
        val = value.bytes_val
    elif value.HasField("decimal_val"):
        val = value.decimal_val
    elif value.HasField("float_val"):
        val = value.float_val
    elif value.HasField("int_val"):
        val = value.int_val
    elif value.HasField("json_ietf_val"):
        val = json.loads(decode_bytes(value.json_ietf_val))
    elif value.HasField("json_val"):
        val = json.loads(decode_bytes(value.json_val))
    elif value.HasField("leaflist_val"):
        lst = []
        for elem in value.leaflist_val.element:
            lst.append(extract_value_v4(elem))
        val = lst
    elif value.HasField("proto_bytes"):
        val = value.proto_bytes
    elif value.HasField("string_val"):
        val = value.string_val
    elif value.HasField("uint_val"):
        val = value.uint_val
    else:
        raise ValueError("Unhandled type of value %s" % str(value))

    return val


def format_version():
    elems = (_PROG_NAME, __version__,
             google.protobuf.__version__, grpc.__version__)
    return "%s %s [protobuf %s, grpcio %s]" % elems


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--version", action="version",
                        version=format_version())
    parser.add_argument("target", default="127.0.0.1:6030",
                        help="gNMI gRPC server (default: localhost:6030)")
    parser.add_argument("paths", nargs="*", default=["/"])

    group = parser.add_argument_group()
    group.add_argument("-d", "--debug", action="store_true",
                       help="enable gRPC debugging")

    group = parser.add_argument_group()
    group.add_argument("-u", "--username", default="admin")
    group.add_argument("-p", "--password", default="")

    group = parser.add_argument_group("Path options")
    group.add_argument("--origin", default=None, type=str,
                       help="ex. (--origin eos_native)")

    group = parser.add_argument_group("Subscribe options")
    group.add_argument("--interval", default=None, type=str,
                       help="sample interval in milliseconds (default: 10s)")
    group.add_argument("--timeout", default=None, type=str,
                       help="subscription duration in milliseconds (default: None)")
    group.add_argument("--heartbeat", default=None, type=str,
                       help="heartbeat interval in milliseconds (default: None)")
    group.add_argument("--aggregate", action="store_true",
                       help="allow aggregation")
    group.add_argument("--suppress", action="store_true",
                       help="suppress redundant")
    group.add_argument("--submode", default="on-change", type=str,
                       help="subscription mode [target-defined, on-change, sample]")
    group.add_argument("--mode", default="stream", type=str,
                       help="[stream, once, poll]")
    group.add_argument("--qos", default=0, type=int,
                       help="DSCP value to be set on transmitted telemetry")

    group.add_argument("--use-alias", action="store_true", help="use aliases")

    group.add_argument("--encoding", default="json", type=str,
                       help="[json, bytes, proto, ascii, json-ietf]")
    group.add_argument("--prefix", default="", type=str,
                       help="gRPC path prefix (default: none)")

    return parser.parse_args()


def parse_duration(duration):

    multipliers = {
        "n": 1,
        "u": 1000,
        "m": 1000000,
        "ms": 1000000,
        "s": 1000000000
    }

    if duration is None:
        return None

    match = re.match(r'(?P<value>\d+)(?P<unit>[a-z]+)?', duration)

    val = int(match.group("value"))
    unit = match.group("unit") or "m"

    if unit not in multipliers:
        raise ValueError("Invalid unit in duration: %s" % duration)

    return val * multipliers[unit]


def parse_path(path):
    names = []
    path = path.strip().strip("/")
    if not path or path == "/":
        names = []
    else:
        names = [re.sub(r"\\", "", n) for n in re.split(r"(?<!\\)/", path)]

    elems = []
    for name in names:
        match = _RE_PATH_COMPONENT.search(name)
        if not match:
            raise ValueError("path component parse error: %s" % name)

        if match.group("key") is not None:
            tmp_key = {}
            for keyval in re.findall(r"\[([^]]*)\]", name):
                val = keyval.split("=")[-1]
                tmp_key[keyval.split("=")[0]] = val

            pname = match.group("pname")
            elem = pb.PathElem(name=pname, key=tmp_key)
            elems.append(elem)
        else:
            elems.append(pb.PathElem(name=name, key={}))

    return pb.Path(elem=elems)


def str_path(path):
    strpath = "/"

    if not path:
        pass
    elif len(path.elem) > 0:
        strpath = str_path_v4(path)
    elif len(path.element) > 0:
        strpath = str_path_v3(path)
    return strpath


def str_path_v3(path):
    print(path.element)
    return "/" + "/".join(path.element)


def str_path_v4(path):
    strpath = ""
    for elem in path.elem:
        strpath += "/" + escape_string(elem.name, "/")
        for key, val in elem.key.items():
            val = escape_string(val, "]")
            strpath += "[" + key + "=" + val + "]"

    return strpath


def enable_debuging():
    os.environ['GRPC_TRACE'] = 'all'
    os.environ['GRPC_VERBOSITY'] = 'DEBUG'

def main():

    args = parse_args()

    if args.debug:
        enable_debuging()

    target = args.target

    origin = args.origin
    prefix = args.prefix
    prefix = parse_path(prefix)
    # print(_prefix)

    paths = args.paths
    username = args.username
    password = args.password

    encoding = None
    if args.encoding == "json":
        encoding = pb.JSON_IETF
    elif args.encoding == "bytes":
        encoding = pb.BYTES
    elif args.encoding == "proto":
        encoding = pb.PROTO
    elif args.encoding == "ascii":
        encoding = pb.ASCII
    elif args.encoding == "json-ietf":
        encoding = pb.JSON_IETF
    else:
        raise ValueError("Invalid encoding %s" % str(args.encoding))

    # subscribe options
    timeout = args.timeout
    suppress = args.suppress
    interval = parse_duration(args.interval)
    heartbeat = parse_duration(args.heartbeat)
    aggregate = args.aggregate
    use_alias = args.use_alias

    qos = None
    if args.qos is not None:
        qos = pb.QOSMarking(marking=0)

    submode = None
    if args.submode == "target-defined":
        submode = pb.TARGET_DEFINED
    elif args.submode == "on-change":
        submode = pb.ON_CHANGE
    elif args.submode == "sample":
        submode = pb.SAMPLE
    else:
        raise ValueError("Invalid subscription mode %s" % str(args.submode))

    mode = None
    if args.mode == "stream":
        mode = 0
    elif args.mode == "once":
        mode = 1
    elif args.mode == "poll":
        mode = 2
    else:
        raise ValueError("Invalid mode %s" % str(args.mode))


    channel = grpc.insecure_channel(target)
    stub = gnmi_pb2_grpc.gNMIStub(channel)

    paths = [parse_path(path) for path in paths]

    subs = []
    for path in paths:

        if origin:
            path.origin = origin

        sub = pb.Subscription(path=path, mode=submode,
                                suppress_redundant=suppress,
                                sample_interval=interval,
                                heartbeat_interval=heartbeat)
        subs.append(sub)

    def _sr():

        sub_list = pb.SubscriptionList(prefix=prefix, mode=mode,
                                         allow_aggregation=aggregate,
                                         encoding=encoding, subscription=subs,
                                         use_aliases=use_alias, qos=qos)
        req_iter = pb.SubscribeRequest(subscribe=sub_list)
        yield req_iter

    try:
        responses = stub.Subscribe(_sr(), timeout, metadata=[
            ("username", username), ("password", password)])
        for response in responses:

            if response.HasField("sync_response"):
                pass
            elif response.HasField("error"):
                print("gNMI Error " + str(response.error.code) +
                      " received\n" + str(response.error.message))
            elif response.HasField("update"):
                prefix = str_path(q)

                if prefix == "/":
                    prefix = ""

                for update in response.update.update:
                    path = prefix + str_path(update.path)
                    value = extract_value(update)

                    print("%s = %s" % (path, str(value)))
            else:
                print("Unknown response received:\n" + str(response))

    except KeyboardInterrupt:
        print("stopped by user")

    except grpc.RpcError as err:
        print("grpc.RpcError received:\n%s" % err)


if __name__ == "__main__":
    main()
