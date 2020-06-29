# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.
"""
gnmi.messages
~~~~~~~~~~~~~~~~

gNMI messags wrappers

"""

import re
import collections
import json
import sys

from abc import ABCMeta, abstractmethod
from typing import List, Tuple, Any

import google.protobuf as _
import grpc

from gnmi.proto import gnmi_pb2 as pb  # type: ignore
from gnmi import util

# def _cast_gnmi_type(value, gnmi_type):
#     pass
    
class BaseMessage(metaclass=ABCMeta):

    def __init__(self, message):
        self.raw = message

class IterableMessage(BaseMessage):

    def __iter__(self):
        return self.iterate()

    @abstractmethod
    def iterate(self):
        yield from ()

    def collect(self):
        """Collect"""
        collected = []
        for item in self:
            if isinstance(item, IterableMessage):
                item = item.collect()
            collected.append(item)
        return collected

class CapabilitiesResponse_(BaseMessage):
    r"""Represents a gnmi.CapabilitiesResponse message

    """

    @property
    def supported_models(self):
        for model in self.raw.supported_models:
            yield {
                "name": model.name,
                "organization": model.organization,
                "version": model.version
            }
    models = supported_models

    @property
    def supported_encodings(self):
        return self.raw.supported_encodings
    encodings = supported_encodings

    @property
    def gnmi_version(self):
        return self.raw.gNMI_version
    version = gnmi_version


class Update_(BaseMessage):
    r"""Represents a gnmi.Update message

    """

    _TYPED_VALUE_MAP = {
        bool: 'bool_val',
        dict: 'json_ietf_val',
        int: 'int_val',
        float: 'float_val',
        str: 'string_val'
    }

    _TYPE_HANDLER_MAP = {
        'bool_val': lambda value: True if value else False,
        'json_ietf_val': lambda value: json.dumps(value).encode(),
        'json_val': lambda value: json.dumps(value).encode(),
        'int_val': int,
        'float_val': float,
        'string_val': str
    }
    
    @property
    def path(self):
        return Path_(self.raw.path)

    @property
    def value(self):
        return util.extract_value(self.raw)
    val = value
    
    @property
    def duplicates(self):
        return self.raw.duplicates

    @classmethod
    def from_keyval(cls, keyval: Tuple[str, Any], forced_type: str = ""):
        path, value = keyval

        path = Path_.from_string(path)
        typed_value = pb.TypedValue()

        type_: str = forced_type
        func = lambda v: v
        
        if forced_type:
            func = cls._TYPE_HANDLER_MAP.get(forced_type, lambda v: v)
        else:
            type_ = cls._TYPED_VALUE_MAP.get(type(value))
            if not type_:
                raise ValueError("Invalid type: %s for %s" % type(value), str(value))
            func = cls._TYPE_HANDLER_MAP[type_]
        
        setattr(typed_value, type_, func(value))
        
        return cls(pb.Update(path=path.raw, val=typed_value))


class Notification_(IterableMessage):
    r"""Represents a gnmi.Notification message

    """
    
    def iterate(self):
        return self.updates

    @property
    def prefix(self):
        return Path_(self.raw.prefix)
    
    @property
    def timestamp(self):
        return self.raw.timestamp

    @property
    def updates(self):
        for update in self.raw.update:
            yield Update_(update)

class GetResponse_(IterableMessage):
    r"""Represents a gnmi.GetResponse message

    """

    def iterate(self):
        return self.notifications
    
    @property
    def notifications(self):
        for notification in self.raw.notification:
            yield Notification_(notification)

class UpdateResult_(BaseMessage):
    _OPERATION = [
        "INVALID",
        "DELETE",
        "REPLACE",
        "UPDATE"
    ]
    
    def __str__(self):
        return "%s %s" % (self.operation, self.path)
    
    @property
    def op(self):
        #return self._OPERATION.index(self.raw.operation) 
        
        return self._OPERATION[self.raw.op]
    operation = op
    
    @property
    def path(self):
        return Path_(self.raw.path)

class SetResponse_(IterableMessage):

    def iterate(self):
        return self.responses
    
    @property
    def timetamp(self):
        pass

    @property
    def responses(self):
        for resp in self.raw.response:
            yield UpdateResult_(resp)

class SubscribeResponse_(BaseMessage):
    r"""Represents a gnmi.SubscribeResponse message

    """

    # @property
    # def sync_response(self):
    #     pass
    @property
    def sync_response(self) -> bool:
        return self.raw.sync_response

    @property
    def update(self):
        return Notification_(self.raw.update)

class PathElem_(BaseMessage):
    r"""Represents a gnmi.PathElem message

    """
    
    @property
    def key(self):
        if hasattr(self.raw, "key"):
            return self.raw.key 
        return {}

    @property
    def name(self):
        return self.raw.name

class Path_(BaseMessage):
    r"""Represents a gnmi.Path message

    """

    RE_ORIGIN = re.compile(r"(?:(?P<origin>[\w\-]+)?:)?(?P<path>\S+)$")
    
    def __str__(self):
        return self.to_string()
    
    def __add__(self, other: 'Path_') -> 'Path_':
        elems = []

        for elem in self.elements:
            elems.append(elem.raw)

        for elem in other.elements:
            elems.append(elem.raw)

        return Path_(pb.Path(elem=elems)) # type: ignore


    @property
    def elements(self):
        elem = self.raw.elem
        
        # use v3 if present
        if len(self.raw.element) > 0:
            elem = self.raw.element
        
        for elem in self.raw.elem:
            yield PathElem_(elem)

    @property
    def origin(self):
        return self.raw.origin
    
    @property
    def target(self):
        return self.raw.target

    def to_string(self):

        path = ""
        for elem in self.elements:
            path += "/" + util.escape_string(elem.name, "/")
            for key, val in elem.key.items():
                val = util.escape_string(val, "]")
                path += "[" + key + "=" + val + "]"

        if self.origin:
            path = ":".join([self.origin, path])
        
        return path
    
    @classmethod
    def from_string(cls, path):

        if not path:
            return cls(pb.Path(origin=None, elem=[])) # type: ignore
        
        names: List[str] = []
        elems: list = []
        
        path = path.strip()
        origin = None

        match = cls.RE_ORIGIN.search(path)
        origin = match.group("origin")
        path = match.group("path")
        
        for elem in util.parse_path(path):
            elems.append(pb.PathElem(name=elem["name"], key=elem["keys"])) # type: ignore

        return cls(pb.Path(origin=origin, elem=elems)) # type: ignore

class Status_(collections.namedtuple('Status_', 
        ('code', 'details', 'trailing_metadata')), grpc.Status):
    
    @classmethod
    def from_call(cls, call):
        return cls(call.code(), call.details(), call.trailing_metadata())
