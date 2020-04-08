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

from gnmi.messages import Path_

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
    if sys.version_info < (3, 6, 0):
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
    update.value
    try:
        val = extract_value_v4(update.val)
    except ValueError:
        val = extract_value_v3(update.value)

    return val


def extract_value_v3(value):
    val = None
    if value.type in (pb.JSON_IETF, pb.JSON): # type: ignore
        val = json.loads(decode_bytes(value.value))
    elif value.type in (pb.BYTES, pb.PROTO): # type: ignore
        val = value.value
    elif value.type == pb.ASCII: # type: ignore
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
            elem = pb.PathElem(name=pname, key=tmp_key) # type: ignore
            elems.append(elem)
        else:
            elems.append(pb.PathElem(name=name, key={})) # type: ignore

    return pb.Path(elem=elems) # type: ignore


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

def get_gnmi_constant(name):
    return getattr(pb, name.replace("-", "_").upper())

def path_join(paths: List[Any]) -> Path_:

    

    for path in paths:
        if isinstance(path, str):
            path = Path_.from_string(path)
        elif isinstance(path, pb.Path):
            path = Path_(path)
        elif isinstance(path, Path_):
            pass
        else:
            raise ValueError("Failed to parse path: %s" % str(path))
    
    #return "/".join([p.strip().strip("/") for p in list(args) ])