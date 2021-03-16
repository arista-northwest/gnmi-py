# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.
"""
gnmi.messages
~~~~~~~~~~~~~~~~

gNMI messags wrappers

"""

import collections
import functools
import itertools
import json
import re
import warnings

from abc import ABCMeta, abstractmethod
from typing import Any, Generator, List, Optional, Tuple, Union

import google.protobuf as _
import grpc

from gnmi.environments import GNMI_NO_DEPRECATED, GNMI_RC_PATH
from gnmi.exceptions import GnmiDeprecationError
from gnmi.proto import gnmi_pb2 as pb  # type: ignore
from gnmi import util

warnings.simplefilter("once", category=(PendingDeprecationWarning, DeprecationWarning))

def deprecated(msg, klass=DeprecationWarning):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if GNMI_NO_DEPRECATED:
                raise GnmiDeprecationError(msg)
            warnings.warn(msg, klass, stacklevel=2)
            return func(*args, **kwargs)
        return wrapper
    return decorator

class BaseMessage(metaclass=ABCMeta):

    def __init__(self, message):
        self.raw = message

class IterableMessage(BaseMessage):

    @abstractmethod
    def __iter__(self):
        return iter([])

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

@deprecated(("Deprecated in favour of using the "
    "google.golang.org/genproto/googleapis/rpc/status"
    "message in the RPC response."))
class Error_(BaseMessage):
    
    @property
    def code(self) -> int:
        return self.raw.code
    
    @property
    def message(self) -> str:
        return self.raw.message

    @property
    def data(self) -> Any:
        return self.raw.data

class TypedValue_(BaseMessage):

    @property
    def value(self) -> Any:
        return self.extract_val()

    def __str__(self):
        return str(self.extract_val())

    def extract_val(self) -> Any:
        val = None
        if self.raw.HasField("any_val"):
            val = self.raw.any_val
        elif self.raw.HasField("ascii_val"):
            val = self.raw.ascii_val
        elif self.raw.HasField("bool_val"):
            val = self.raw.bool_val
        elif self.raw.HasField("bytes_val"):
            val = self.raw.bytes_val
        elif self.raw.HasField("decimal_val"):
            val = self.raw.decimal_val
        elif self.raw.HasField("float_val"):
            val = self.raw.float_val
        elif self.raw.HasField("int_val"):
            val = self.raw.int_val
        elif self.raw.HasField("json_ietf_val"):
            val = json.loads(self.raw.json_ietf_val)
        elif self.raw.HasField("json_val"):
            val = json.loads(self.raw.json_val)
        elif self.raw.HasField("leaflist_val"):
            lst = []
            for elem in self.raw.leaflist_val.element:
                lst.append(TypedValue_(elem).extract_val())
            val = lst
        elif self.raw.HasField("proto_bytes"):
            val = self.raw.proto_bytes
        elif self.raw.HasField("string_val"):
            val = self.raw.string_val
        elif self.raw.HasField("uint_val"):
            val = self.raw.uint_val
        else:
            raise ValueError("Unhandled typed value %s" % self.raw)

        return val

@deprecated("Message 'Value' is deprecated and may be removed in the future")
class Value_(BaseMessage):

    @property
    def value(self):
        return self.extract_val()

    @property
    def type(self):
        return self.raw.type

    def __str__(self):
        return str(self.extract_val())

    def extract_val(self) -> Any:
        val = None
        if self.type in (pb.JSON_IETF, pb.JSON) and self.raw.value:
            val = json.loads(self.raw.value)
        elif self.type in (pb.BYTES, pb.PROTO):
            val = self.raw.value
        elif self.type == pb.ASCII:
            val = str(self.raw.value)
        else:
            raise ValueError("Unhandled type of value %s" % str(val))
        return val

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
    def val(self) -> Optional[TypedValue_]:
        if self.raw.HasField('val'):
            return TypedValue_(self.raw.val)
    
    @property
    def value(self) -> Optional[Value_]:
        if self.raw.HasField('value'):
            return Value_(self.raw.value)
    
    @property
    def duplicates(self):
        return self.raw.duplicates

    def get_value(self) -> Union[TypedValue_, Value_]:
        if self.val:
            return self.val.extract_val()
        elif self.value:
            return self.value.extract_val()

    @classmethod
    def from_keyval(cls, keyval: Tuple[str, Any], forced_type: str = ""):
        path, value = keyval

        path = Path_.from_string(path)
        typed_value = pb.TypedValue()

        type_: Optional[str] = forced_type
        func = lambda v: v
        
        if forced_type:
            func = cls._TYPE_HANDLER_MAP.get(forced_type, lambda v: v)
        else:
            type_ = cls._TYPED_VALUE_MAP.get(type(value))
            if not type_:
                raise ValueError(f"Invalid type: {type(value)} for {value.raw}")
            func = cls._TYPE_HANDLER_MAP[type_]
        
        setattr(typed_value, type_, func(value))
        
        return cls(pb.Update(path=path.raw, val=typed_value))


class Notification_(IterableMessage):
    r"""Represents a gnmi.Notification message

    """
    
    def __iter__(self):
        return self.update

    @property
    def prefix(self):
        return Path_(self.raw.prefix)
    
    @property
    def timestamp(self):
        return self.raw.timestamp

    @property
    def update(self) -> Generator[Update_, None, None]:
        for u in self.raw.update:
            yield Update_(u)

    updates = update

class GetResponse_(IterableMessage):
    r"""Represents a gnmi.GetResponse message

    """

    def __iter__(self):
        return self.notification

    @property
    def notification(self):
        for notification in self.raw.notification:
            yield Notification_(notification)
    notifications = notification
        
    @property
    def error(self) -> Error_:
        if self.raw.HasField('error'):
            return Error_(self.raw.error)

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

    @property
    @deprecated(("Deprecated timestamp for the UpdateResult, this field has been "
        "replaced by the timestamp within the SetResponse message, since "
        "all mutations effected by a set should be applied as a single "
        "transaction."))
    def timestamp(self) -> int:
        return self.raw.timestamp

    @property
    def error(self) -> Optional[Error_]:
        if self.raw.HasField('error'):
            return Error_(self.raw.error)

class SetResponse_(IterableMessage):

    def __iter__(self):
        return self.response

    @property
    def timetamp(self):
        pass

    @property
    def response(self):
        for resp in self.raw.response:
            yield UpdateResult_(resp)

    responses = response

    @property
    def error(self) -> Optional[Error_]:
        if self.raw.HasField('error'):
            return Error_(self.raw.error)

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

    @property
    def error(self) -> Optional[Error_]:
        if self.raw.HasField('error'):
            return Error_(self.raw.error)

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

class Path_(IterableMessage):
    r"""Represents a gnmi.Path message

    """

    RE_ORIGIN = re.compile(r"(?:(?P<origin>[\w\-]+)?:)?(?P<path>\S+)$")
    
    def __str__(self):
        return self.to_string()
    
    def __add__(self, other: 'Path_') -> 'Path_':
        elems = []
        elements = []

        for e in itertools.chain(self.elem, other.elem):
            elems.append(e.raw)

        if not elems:
            for e in itertools.chain(self.element, other.element):
                elements.append(e)

        return Path_(pb.Path(elem=elems, element=elements)) # type: ignore

    def __iter__(self):
        return self.elem

    @property
    def elem(self) -> Generator[PathElem_, None, None]:
        for elem in self.raw.elem:
            yield PathElem_(elem)
    elems = elem

    @property
    def element(self) -> Generator[str, None, None]:
        for e in self.raw.element:
            warnings.warn("Field 'element' has been deprecated and may be removed in the future",
                DeprecationWarning, stacklevel=2)
            yield e
    elements = element

    @property
    def origin(self):
        return self.raw.origin
    
    @property
    def target(self):
        return self.raw.target

    def to_string(self):

        path = ""
        for elem in self.elem:
            path += "/" + util.escape_string(elem.name, "/")
            for key, val in elem.key.items():
                val = util.escape_string(val, "]")
                path += "[" + key + "=" + val + "]"

        if not path:
            path =  "/" + "/".join(self.element)

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
