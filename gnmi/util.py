# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import os
import sys
import re
import json
from typing import Any, List
import google.protobuf as _
import gnmi.proto.gnmi_pb2 as pb  # type: ignore

# from gnmi.messages import Path_

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


def enable_debuging():
    os.environ['GRPC_TRACE'] = 'all'
    os.environ['GRPC_VERBOSITY'] = 'DEBUG'

def get_gnmi_constant(name):
    return getattr(pb, name.replace("-", "_").upper())
