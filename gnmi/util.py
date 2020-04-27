# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import json
import os
import re
import pathlib

from configparser import ConfigParser
import google.protobuf as _
import gnmi.proto.gnmi_pb2 as pb  # type: ignore

import gnmi.environments

from gnmi.config import Config
from gnmi.constants import GNMIRC_FILES


RE_PATH_COMPONENT = re.compile(r'''
^
(?P<name>[^[]+)
(?P<keyval>\[.*\])?$
''', re.VERBOSE)


def enable_debuging():
    os.environ['GRPC_TRACE'] = 'all'
    os.environ['GRPC_VERBOSITY'] = 'DEBUG'


def get_gnmi_constant(name):
    return getattr(pb, name.replace("-", "_").upper())

def load_rc():
    rc = Config({})
    path = pathlib.Path(gnmi.environments.RC_PATH)
    for name in GNMIRC_FILES:
        fil = path / name
        if fil.exists():
            return Config.load(fil)
    return rc


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
    parsed = []
    elems = [re.sub(r"\\", "", name) for name in re.split(r"(?<!\\)/", path) if name]

    for elem in elems:
        keys = {}
        match = RE_PATH_COMPONENT.search(elem)
        name = match.group("name")
        keyvals = match.group("keyval")
        if keyvals:
            for keyval in re.findall(r"\[([^]]*)\]", keyvals):
                key, val = keyval.split("=")
                keys[key] = val

        parsed.append(dict(name=name, keys=keys))
    
    return parsed

def prepare_metadata(data):
    # normailize metadata to a list of tuples
    ndata = []

    for key, val in data.items():
        ndata.append((key, val))
    return [(k, v) for k,v in data.items()]

def escape_string(string, escape):
    result = ""
    for character in string:
        if character in tuple(escape) + ("\\",):
            result += "\\"
        result += character
    return result


def extract_value(value):
    if not value:
        return value
    
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
        val = json.loads(value.json_ietf_val)
    elif value.HasField("json_val"):
        val = json.loads(value.json_val)
    elif value.HasField("leaflist_val"):
        lst = []
        for elem in value.leaflist_val.element:
            lst.append(extract_value(elem))
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