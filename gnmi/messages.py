# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.
"""
gnmi.messages
~~~~~~~~~~~~~~~~

gNMI messags wrappers

"""

import base64
import collections
import functools
import itertools
import json
import re
import warnings
import enum
from abc import ABCMeta, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Generator, List, Optional, Tuple, Union

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

    # @abstractmethod
    # def to_dict(self): ...

class IterableMessage(BaseMessage):

    @abstractmethod
    def __iter__(self):
        return iter([])

    def collect(self) -> list:
        """Collect"""
        collected = []
        for item in self:
            if isinstance(item, IterableMessage):
                item = item.collect()
            collected.append(item)
        return collected


class Notification_(IterableMessage):
    r"""Represents a gnmi.Notification message

    """
    
    def __iter__(self) -> Generator[Union['Update_', 'Path_'], None, None]:
        return itertools.chain(self.update, self.delete)

    @property
    def atomic(self) -> bool:
        return self.raw.atomic

    @property
    def prefix(self) -> 'Path_':
        return Path_(self.raw.prefix)
    
    @property
    def timestamp(self) -> int:
        return self.raw.timestamp

    @property
    def time(self) -> datetime:
        return util.datetime_from_int64(self.timestamp)
        
    @property
    def update(self) -> Generator['Update_', None, None]:
        for u in self.raw.update:
            yield Update_(u)
    updates = update

    @property
    def delete(self) -> Generator['Path_', None, None]:
        for path in self.raw.delete:
            yield Path_(path)
    deletes = delete

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
    def path(self) -> 'Path_':
        return Path_(self.raw.path)

    @property
    def val(self) -> Optional['TypedValue_']:
        if self.raw.HasField('val'):
            return TypedValue_(self.raw.val)
    
    @property
    def value(self) -> Optional['Value_']:
        if self.raw.HasField('value'):
            return Value_(self.raw.value)
    
    @property
    def duplicates(self) -> int:
        return self.raw.duplicates

    def get_value(self) -> Union['TypedValue_', 'Value_']:
        if self.val:
            return self.val.extract_val()
        elif self.value:
            return self.value.extract_val()

    @classmethod
    def from_keyval(cls, keyval: Tuple[str, Any], forced_type: str = "") -> 'Update_':
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
            val = base64.b64encode(self.raw.bytes_val)
        elif self.raw.HasField("decimal_val"):
            val = self.raw.decimal_val
            val = Decimal(str(val.digits / 10**val.precision))
        elif self.raw.HasField("float_val"):
            val = self.raw.float_val
        elif self.raw.HasField("int_val"):
            val = self.raw.int_val
        elif self.raw.HasField("json_ietf_val"):
            val = json.loads(self.raw.json_ietf_val)
        elif self.raw.HasField("json_val"):
            val = json.loads(self.raw.json_val)
        elif self.raw.HasField("leaflist_val"):
            val = []
            for elem in self.raw.leaflist_val.element:
                val.append(TypedValue_(elem).extract_val())
        elif self.raw.HasField("proto_bytes"):
            val = self.raw.proto_bytes
        elif self.raw.HasField("string_val"):
            val = self.raw.string_val
        elif self.raw.HasField("uint_val"):
            val = self.raw.uint_val
        else:
            raise ValueError("Unhandled typed value %s" % self.raw)

        return val

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
    def elem(self) -> Generator['PathElem_', None, None]:
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
    def origin(self) -> str:
        return self.raw.origin
    
    @property
    def target(self) -> str:
        return self.raw.target

    def to_string(self) -> str:

        path = ""
        for elem in self.elem:
            path += "/" + util.escape_string(elem.name, "/")
            for key, val in elem.key.items():
                val = util.escape_string(val, "]")
                path += "[" + key + "=" + val + "]"

        if not path and self.element:
            path =  "/".join(self.element)

        if self.origin:
            path = ":".join([self.origin, path])
        return path
    
    @classmethod
    def from_string(cls, path: str) -> 'Path_':

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

class PathElem_(BaseMessage):
    r"""Represents a gnmi.PathElem message

    """
    
    @property
    def key(self) -> Dict[str, str]:
        if hasattr(self.raw, "key"):
            return self.raw.key 
        return {}

    @property
    def name(self) -> str:
        return self.raw.name

@deprecated("Message 'Value' is deprecated and may be removed in the future")
class Value_(BaseMessage):

    @property
    def value(self) -> Any:
        return self.extract_val()

    @property
    def type(self) -> 'Encoding_':
        return Encoding_(self.raw.type)

    def __str__(self):
        return str(self.extract_val())

    def extract_val(self) -> Any:
        if self.type.name in ('JSON_IETF', 'JSON') and self.raw.value:
            return json.loads(self.raw.value)
        elif self.type.name in ('BYTES', 'PROTO'):
            return base64.b64encode(self.raw.value)
        elif self.type.name == 'ASCII':
            return str(self.raw.value)
        
        raise ValueError("Unhandled type of value %s" % str(self.raw.value))

class Encoding_(enum.Enum):
    JSON = 0
    BYTES = 1
    PROTO = 2
    ASCII = 3
    JSON_IETF = 4

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

class SubscribeResponse_(BaseMessage):
    r"""Represents a gnmi.SubscribeResponse message

    """
    
    @property
    def sync_response(self) -> bool:
        return self.raw.sync_response

    @property
    def update(self) -> Notification_:
        return Notification_(self.raw.update)
    notification = update

    @property
    def error(self) -> Optional[Error_]:
        if self.raw.HasField('error'):
            return Error_(self.raw.error)

class SetResponse_(IterableMessage):

    def __iter__(self):
        return self.response

    @property
    def timetamp(self) -> int:
        return self.raw.timestamp

    @property
    def time(self) -> datetime:
        return util.datetime_from_int64(self.timestamp)

    @property
    def response(self):
        for resp in self.raw.response:
            yield UpdateResult_(resp)

    responses = response

    @property
    def error(self) -> Optional[Error_]:
        if self.raw.HasField('error'):
            return Error_(self.raw.error)

class UpdateResult_(BaseMessage):

    class Operation_(enum.Enum):
        INVALID = 0
        DELETE = 1
        REPLACE = 2
        UPDATE = 3
    
    def __str__(self):
        return "%s %s" % (self.operation, self.path)
    
    @property
    def op(self) -> enum.Enum:
        return self.Operation_(self.raw.op)
    operation = op
    
    @property
    def path(self) -> Path_:
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

class GetResponse_(IterableMessage):
    r"""Represents a gnmi.GetResponse message

    """

    def __iter__(self):
        return self.notification

    @property
    def notification(self) -> Generator[Notification_, None, None]:
        for notification in self.raw.notification:
            yield Notification_(notification)
    notifications = notification
        
    @property
    def error(self) -> Optional[Error_]:
        if self.raw.HasField('error'):
            return Error_(self.raw.error)

class CapabilitiesResponse_(BaseMessage):
    r"""Represents a gnmi.CapabilitiesResponse message

    """

    @property
    def supported_models(self) -> Generator[dict, None, None]:
        for model in self.raw.supported_models:
            yield {
                "name": model.name,
                "organization": model.organization,
                "version": model.version
            }
    models = supported_models

    @property
    def supported_encodings(self) -> List[Encoding_]:
        return [Encoding_(i) for i in self.raw.supported_encodings]
    encodings = supported_encodings

    @property
    def gnmi_version(self) -> str:
        return self.raw.gNMI_version
    version = gnmi_version

class Status_(collections.namedtuple('Status_', 
        ('code', 'details', 'trailing_metadata')), grpc.Status):
    
    @classmethod
    def from_call(cls, call) -> 'Status_':
        return cls(call.code(), call.details(), call.trailing_metadata())