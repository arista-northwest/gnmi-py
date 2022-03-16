# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import argparse
import json
import os
import signal
import sys

from grpc import __version__ as grpc_version
from google.protobuf import __version__ as pb_version

from gnmi.config import Config
from gnmi.messages import Notification_
from gnmi.session import Session
from gnmi.structures import CertificateStore, GetOptions, GrpcOptions, SubscribeOptions, Target
from gnmi.exceptions import GrpcDeadlineExceeded
from gnmi import util
import gnmi


def signal_handler(signal, frame):
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def format_version():
    elems = (gnmi.__version__, pb_version, grpc_version)
    return "gnmipy %s [protobuf %s, grpcio %s]" % elems

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--version", action="version",
                        version=format_version())
    parser.add_argument("target", help="gNMI gRPC server")
    parser.add_argument("operation", type=str, choices=['capabilities', 'get', 'subscribe'],
        help="gNMI operation [capabilities, get, subscribe]")
    parser.add_argument("paths", nargs="*", default=[])

    parser.add_argument("-c", "--config", type=str, default=None,
        help="Path to gNMI config file")

    group = parser.add_argument_group()
    group.add_argument("--debug-grpc", action="store_true",
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
    group.add_argument("--mode", default=None, type=str, choices=['stream', 'once', 'poll'],
                       help="Specify subscription mode")
    group.add_argument("--submode", default=None, type=str, choices=['target-defined', 'on-change', 'sample'],
                       help="subscription sub-mode")
    group.add_argument("--once", action="store_true", default=False,
                       help=("End subscription after first sync_response. This is a "
                             "workaround for implementions that do not support 'once' "
                             "subscription mode"))
    group.add_argument("--qos", default=0, type=int,
                       help="DSCP value to be set on transmitted telemetry")

    group.add_argument("--use-alias", action="store_true", help="use aliases")

    group.add_argument("--tls-ca", default="", type=str, help="")
    group.add_argument("--tls-cert", default="", type=str, help="")
    group.add_argument("--tls-key", default="", type=str, help="")
    group.add_argument("--insecure", action="store_true", help="disable TLS")

    group.add_argument("--host-override", default=None,
        help="Override gRPC server hostname")
    #group.add_argument("--tls-no-verify", action="store_true", help="")
    
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
    _operation["options"] = {}
    if args.prefix:
        _operation["options"]["prefix"] = args.prefix

    if args.encoding:
        _operation["options"]["encoding"] = args.encoding
    
    if operation_name == "Get":
        if args.get_type:
            _operation["options"]["type"] = args.get_type
    
    elif operation_name == "Subscribe":
        if args.heartbeat:
            _operation["options"]["heartbeat"] = util.parse_duration(args.heartbeat)
        
        if args.interval:
            _operation["options"]["interval"] = util.parse_duration(args.interval)

        if args.mode:
             _operation["options"]["mode"] = args.mode
        if args.qos:
            _operation["options"]["qos"] = args.qos
        
        if args.submode:
            _operation["options"]["submode"] = args.submode
        
        if args.suppress:
            _operation["options"]["suppress"] = args.suppress
        
        if args.timeout:
            _operation["options"]["timeout"] = args.timeout
        
        if args.use_alias:
            _operation["options"]["use_alias"] = args.use_alias

    return Config(data)

def write_notification(n: Notification_):
    notif = {}

    updates = []
    for u in n.update:
        
        val = u.get_value()
        if isinstance(val, bytes):
            val = val.decode("utf-8")

        updates.append({
            "path": str(u.path),
            "value": val
        })

    deletes = []
    for d in n.delete:
        deletes.append({
            "path": str(d)
        })

    if n.atomic:
        notif["atomic"] = True
    
    prefix = str(n.prefix)
    
    if prefix:
        notif["prefix"] = prefix

    if n.timestamp:
        notif["timestamp"] = n.timestamp
        notif["time"] = n.time.isoformat()

    if updates:
        notif["updates"] = updates

    if deletes:
        notif["deletes"] = deletes
    
    #print(notif)
    print(json.dumps(notif)) #, separators=[", ", ": "], indent=2))

def main():
    args = parse_args()
    config: Config
    rc: Config = util.load_rc()

    config = make_config(args).merge(rc)

    host, port = args.target.split(":")[:2]
    target: Target = (host, int(port))

    if args.debug_grpc:
        util.enable_grpc_debuging()

    cs = CertificateStore()
    if args.tls_ca != "":
        tls_ca = b""
        tls_cert = b""
        tls_key = b""

        with open(args.tls_ca, "rb") as fh:
            tls_ca = fh.read()
        with open(args.tls_cert, "rb") as fh:
            tls_cert = fh.read()
        with open(args.tls_key, "rb") as fh:
            tls_key = fh.read()

        cs = CertificateStore(
            root_certificates=tls_ca,
            certificate_chain=tls_cert,
            private_key=tls_key
        )

    grpc_options={}
    # if args.tls_no_verify:
    #     grpc_options["ssl.server_host_override"] = host

    sess = Session(target, metadata=config.metadata, insecure=args.insecure,
        certificates=cs, grpc_options=grpc_options)

    if config.get("Capabilities"):
        response = sess.capabilities()
        print("gNMI Version: %s" % response.gnmi_version)
        print("Encodings: %s" % ", ".join([i.name for i in response.supported_encodings]))
        print("Models:")
        for model in response.supported_models:
            print("  %s" % model["name"])
            print("    Version:      %s" % model["version"] or "n/a")
            print("    Organization: %s" % model["organization"])
    
    elif config.get("Get") and config["Get"].paths:
        options: GetOptions = config.Get.options
        paths = config.Get.paths
        response = sess.get(paths, options)
        for notif in response:
            write_notification(notif)

    elif config.get("Subscribe") and config["Subscribe"].paths:
        sub_opts: SubscribeOptions = config.Subscribe.options
        paths = config.Subscribe.paths
        try:
            for resp in sess.subscribe(paths, options=sub_opts):
                if resp.sync_response:
                    if args.once:
                        break
                    continue
                write_notification(resp.update)
        except GrpcDeadlineExceeded:
            return

if __name__ == "__main__":
    main()
