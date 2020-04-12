# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import argparse
import os
import signal
import sys

from grpc import __version__ as grpc_version
from google.protobuf import __version__ as pb_version

from gnmi.config import Config
from gnmi.messages import Path_
from gnmi.session import Session
from gnmi.structures import Options, GetOptions, SubscribeOptions, Target
from gnmi.exceptions import GrpcError, GrpcDeadlineExceeded
from gnmi import util
import gnmi


def signal_handler(signal, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def format_version():
    elems = (os.path.basename(__file__), gnmi.__version__,
             pb_version, grpc_version)
    return "%s %s [protobuf %s, grpcio %s]" % elems

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--version", action="version",
                        version=format_version())
    parser.add_argument("target", help="gNMI gRPC server")
    parser.add_argument("operation", type=str, choices=['capabilities', 'get', 'subscribe'],
        help="gNMI operation [capabilities, get, subscribe]")
    parser.add_argument("paths", nargs="*", default=["/"])

    group = parser.add_argument_group()
    group.add_argument("-d", "--debug", action="store_true",
                       help="enable gRPC debugging")

    group = parser.add_argument_group()
    group.add_argument("-u", "--username", default="admin")
    group.add_argument("-p", "--password", default="")
    
    group = parser.add_argument_group("Common options")
    group.add_argument("--encoding", default="json", type=str,
                       choices=["json", "bytes", "proto", "ascii", "json-ietf"],
                       help="set encoding")
    
    group.add_argument("--prefix", default="", type=str,
                       help="gRPC path prefix (default: <empty>)")

    group = parser.add_argument_group("Get options")
    group.add_argument("--get-type", type=str, default=None, choices=["config", "state", "operational"])

    group = parser.add_argument_group("Subscribe options")
    group.add_argument("--interval", default=None, type=str,
                       help="sample interval in milliseconds (default: 10s)")
    group.add_argument("--timeout", default=None, type=int,
                       help="subscription duration in seconds (default: None)")
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


    return parser.parse_args()

def make_config(args) -> Config:

    data = {}
    operation_name = args.operation.capitalize()
    _operation = data[operation_name] = {}
    _metadata = data["metadata"] = {}

    if args.username:
        _metadata["username"] = args.username
        _metadata["password"] = args.password
    

    if operation_name == "Capabilities":
        _operation["exists"] = True
        return Config(data)

    _operation["paths"] = args.paths
    _operation["options"] = {
        "prefix": args.prefix,
        "encoding": args.encoding,
    }
    
    if operation_name == "Get":
        _operation["options"]["type"] = args.get_type
    elif operation_name == "Subscribe":
        _operation["options"].update({
            "heartbeat": util.parse_duration(args.heartbeat),
            "interval": util.parse_duration(args.interval),
            "mode": args.mode,
            "qos": args.qos,
            "submode": args.submode,
            "suppress": args.suppress,
            "timeout": args.timeout,
            "use_alias": args.use_alias
        })

    return Config(data)

def main():
    args = parse_args()
    config: Config = make_config(args)
    
    host, port = args.target.split(":")[:2]
    target: Target = (host, int(port))

    sess = Session(target, metadata=config.metadata)

    if config.get("Capabilities"):
        response = sess.capabilities()
        print("gNMI Version: %s" % response.gnmi_version)
        print("Encodings: %s" % str(response.supported_encodings))
        print("Models:")
        for model in response.supported_models:
            print("  %s" % model["name"])
            print("    Version:      %s" % model["version"] or "n/a")
            print("    Organization: %s" % model["organization"])
    elif config.get("Get"):
        options: GetOptions = config.Get.options
        paths = config.Get.paths
        response = sess.get(paths, options)
        for notif in response:
            prefix = notif.prefix
            for update in notif.updates:
                print("%s = %s" % (prefix + update.path, update.value))
    elif config.get("Subscribe"):
        sub_opts: SubscribeOptions = config.Subscribe.options
        paths = config.Subscribe.paths
        try:
            for resp in sess.subscribe(paths, options=sub_opts):
                prefix = resp.update.prefix
                for update in resp.update.updates:
                    path = prefix + update.path
                    print(str(path), update.value)
        # except KeyboardInterrupt:
        #     pass
        except GrpcDeadlineExceeded:
            return

if __name__ == "__main__":
    main()
