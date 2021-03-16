# -*- coding: utf-8 -*-
# Copyright (c) 2021 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import argparse
from collections import OrderedDict
from gnmi.session import Session
from gnmi.structures import SubscribeOptions, Target

from pprint import pprint

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("target", help="gNMI gRPC server")
    parser.add_argument("paths", nargs="+")
    return parser.parse_args()


def main():
    args = parse_args()
    #print(args)
    host, port = args.target.split(":")
    target: Target = (host, int(port))

    metadata = {
        "username": "admin",
        "password": ""
    }

    results = []

    sess = Session(target, metadata=metadata)

    sub = sess.subscribe(args.paths) #,options=SubscribeOptions(mode="once"))

    for sr in sub:
        if sr.sync_response:
            break

        prefix = sr.update.prefix

        for e in prefix.element:
            results.append((str(prefix), type(prefix.raw).__name__, "element"))
            break

        if sr.error:
            # deprecated error field/message
            results.append((str(prefix), type(sr.raw).__name__, "error"))

        for update in sr.update.updates:
                
            path = prefix + update.path
            for e in path.element:
                results.append((str(path), type(path.raw).__name__, "element"))
                break
            if update.value:
                results.append((str(path), type(update.raw).__name__, "value"))
            
            #print(str(path), update.get_value())

    for l in results:
        print(f"{l[0]},{l[1]},{l[2]}")
if __name__ == "__main__":
    main()