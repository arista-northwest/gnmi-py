#!/usr/bin/env python3

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import json
import re
import os
import sys

import six
import grpc
import gnmi_pb2 as gnmi
import gnmi_pb2_grpc

__version__ = "0.1.2"

_RE_PATH_COMPONENT = re.compile(r'''
^
(?P<pname>[^[]+)
(\[(?P<key>[a-zA-Z0-9\-\/\.]+)
=
(?P<value>.*)
\])?$
    ''', re.VERBOSE)

_PROG_NAME = "gnmi-py"


def _parse_path(path):
    names = []
    path = path.strip().strip("/")
    if not path or path == "/":
        names = []
    else:
        names = re.split(r"(?<!\\)/", path)

    elems = []
    for name in names:
        match = _RE_PATH_COMPONENT.search(name)
        if not match:
            raise ValueError("path component parse error: %s" % name)

        if match.group("key") is not None:
            tmp_key = {}
            for x in re.findall(r"\[([^]]*)\]", name):
                val = x.split("=")[-1]
                val = re.sub(r"\\", "", val)
                tmp_key[x.split("=")[0]] = val

            pname = match.group("pname")
            elem = gnmi.PathElem(name=pname, key=tmp_key)
            elems.append(elem)
        else:
            elems.append(gnmi.PathElem(name=name, key={}))

    return gnmi.Path(elem=elems)


def escape_string(s, esc):
    res = ""
    for c in s:
        if c == esc or c == "\\":
            res += "\\"
        res += c
    return res

# func StrPath(path *pb.Path) string {
# 	if path == nil {
# 		return "/"
# 	} else if len(path.Elem) != 0 {
# 		return strPathV04(path)
# 	} else if len(path.Element) != 0 {
# 		return strPathV03(path)
# 	}
# 	return "/"
# }


def str_path(path):
    if not path:
        return "/"
    elif len(path.elem) > 0:
        return str_path_v4(path)
    elif len(path.element) > 0:
        return str_path_v3(path)
    return "/"


def str_path_v3(path):
    return "/" + "/".join(path.element)


def str_path_v4(path):
    p = ""
    for elem in path.elem:
        p += "/" + escape_string(elem.name, "/")
        # if len(elm.key) > 0:
        for k, v in six.iteritems(elem.key):
            v = escape_string(v, "]")
            p += "[" + k + "=" + v + "]"
    return p

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

    if value.type in (gnmi.JSON_IETF, gnmi.JSON):
        return json.loads(value.value)
    elif value.type in (gnmi.BYTES, gnmi.PROTO):
        return value.value
    elif value.type == gnmi.ASCII:
        return str(value.value)


def extract_value_v4(value):
    if value.HasField("any_val"):
        return value.any_val
    elif value.HasField("ascii_val"):
        return value.ascii_val
    elif value.HasField("bool_val"):
        return value.bool_val
    elif value.HasField("bytes_val"):
        return value.bytes_val
    elif value.HasField("decimal_val"):
        return value.decimal_val
    elif value.HasField("float_val"):
        return value.float_val
    elif value.HasField("int_val"):
        return value.int_val
    elif value.HasField("json_ietf_val"):
        return json.loads(value.json_ietf_val)
    elif value.HasField("json_val"):
        return json.loads(value.json_val)
    elif value.HasField("leaflist_val"):
        res = []
        for elem in value.leaflist_val.element:
            res.append(extract_value(elem))
        return res
    elif value.HasField("proto_bytes"):
        return value.proto_bytes
    elif value.HasField("string_val"):
        return value.string_val
    elif value.HasField("uint_val"):
        return value.uint_val
    else:
        raise ValueError("Unhandled type of value %s", str(value))


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--version", action="version",
                        version="%s %s" % (_PROG_NAME, __version__))
    parser.add_argument("target", default="127.0.0.1:6030",
                        help="gNMI gRPC server (default: localhost:6030)")
    parser.add_argument("paths", nargs="*", default=["/"])

    # group = parser.add_mutually_exclusive_group()
    # group.add_argument("-q", "--quiet",   action="store_true")
    # group.add_argument("-v", "--verbose", action="count")

    group = parser.add_argument_group()
    group.add_argument("-u", "--username", default="admin")
    group.add_argument("-p", "--password", default="")
    # group.add_argument("--cert", metavar="<filename>",  help="CA root certificate")
    # group.add_argument("--tls", action="store_true", help="enable TLS security")
    # group.add_argument("--ciphers", help="override environment "GRPC_SSL_CIPHER_SUITES"")
    # group.add_argument("--alt-name", help="subjectAltName/CN override for server host validation")
    # group.add_argument("--no-host-check",  action="store_true", help="disable server host validation")

    group = parser.add_argument_group()
    group.add_argument("--origin", default=None, type=str,
                       help="ex. (--origin eos_native)")

    group = parser.add_argument_group()
    group.add_argument("--interval", default=None, type=int,
                       help="sample interval (default: 10s)")
    group.add_argument("--timeout", type=int,
                       help="subscription duration in seconds (default: none)")
    group.add_argument("--heartbeat", type=int,
                       help="heartbeat interval (default: none)")
    group.add_argument("--aggregate", action="store_true",
                       help="allow aggregation")
    group.add_argument("--suppress", action="store_true",
                       help="suppress redundant")
    group.add_argument("--submode", default="on-change", type=str,
                       help="subscription mode [target-defined, on-change, sample]")
    group.add_argument("--mode", default="stream", type=str,
                       help="[stream, once, poll]")
    group.add_argument("--encoding", default="json", type=str,
                       help="[json, bytes, proto, ascii, json-ietf]")
    group.add_argument("--qos", default=0, type=int,
                       help="[JSON, BYTES, PROTO, ASCII, JSON_IETF]")
    group.add_argument("--use-alias",  action="store_true", help="use alias")
    group.add_argument("--prefix", default=None,
                       help="gRPC path prefix (default: none)")

    return parser.parse_args()


def main():

    args = parse_args()
    target = args.target  # "192.168.59.14:6030"
    #origin = "eos_native"
    origin = args.origin

    paths = args.paths
    username = args.username
    password = args.password
    timeout = args.timeout

    suppress = args.suppress
    interval = None
    if args.interval is not None:
        interval = args.interval * 1000000000

    heartbeat = args.heartbeat
    prefix = args.prefix
    aggregate = args.aggregate
    use_alias = args.use_alias

    submode = None
    if args.submode == "target-defined":
        submode = gnmi.TARGET_DEFINED
    elif args.submode == "on-change":
        submode = gnmi.ON_CHANGE
    elif args.submode == "sample":
        submode = gnmi.SAMPLE
    else:
        raise ValueError("Invalid subscription mode %s" % str(args.submode))

    encoding = None
    if args.encoding == "json":
        encoding = gnmi.JSON_IETF
    elif args.encoding == "bytes":
        encoding = gnmi.BYTES
    elif args.encoding == "proto":
        encoding = gnmi.PROTO
    elif args.encoding == "ascii":
        encoding = gnmi.ASCII
    elif args.encoding == "json-ietf":
        encoding = gnmi.JSON_IETF
    else:
        raise ValueError("Invalid encoding %s" % str(args.encoding))

    mode = None
    if args.mode == "stream":
        mode = 0
    elif args.mode == "once":
        mode = 1
    elif args.nide == "poll":
        mode = 2
    else:
        raise ValueError("Invalud mode %s" % str(args.mode))

    qos = None
    if args.qos is not None:
        qos = gnmi.QOSMarking(marking=0)

    channel = grpc.insecure_channel(target)
    stub = gnmi_pb2_grpc.gNMIStub(channel)

    subs = []
    for path in paths:
        path = _parse_path(path)

        if origin:
            path.origin = origin

        sub = gnmi.Subscription(path=path, mode=submode,
                                suppress_redundant=suppress,
                                sample_interval=interval,
                                heartbeat_interval=heartbeat)
        subs.append(sub)

    def _sr():
        sub_list = gnmi.SubscriptionList(prefix=prefix, mode=mode,
                                         allow_aggregation=aggregate,
                                         encoding=encoding, subscription=subs,
                                         use_aliases=use_alias, qos=qos)
        req_iter = gnmi.SubscribeRequest(subscribe=sub_list)
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
                prefix = str_path(response.update.prefix)
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

    # except Exception as err:
    #     print(err)


if __name__ == "__main__":
    main()
