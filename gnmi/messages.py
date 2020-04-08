# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import re

from typing import List
import google.protobuf as _

from .proto import gnmi_pb2 as pb  # type: ignore
from gnmi import util

class CapabilitiesResponse_(object):

    def __init__(self, response):
        self.raw = response

    @property
    def supported_models(self):
        for model in self.raw.supported_models:
            yield {
                "name": model.name,
                "orgainization": model.organization,
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

class Update_(object):
    def __init__(self, update):
        self.raw = update

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

class Notification_(object):
    def __init__(self, notification):
        self.raw = notification
    
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

class GetResponse_(object):
    def __init__(self, response):
        self.raw = response

    def __iter__(self):
        return self.notifications

    @property
    def notifications(self):
        for notification in self.raw.notification:
            yield Notification_(notification)


class SubscribeResponse_(object):
    def __init__(self, response):
        self.raw = response

    @property
    def update(self):
        return Notification_(self.raw.update)

class PathElem_(object):
    def __init__(self, elem):
        self.raw = elem
        self.key = {}
        if hasattr(elem, "key"):
            self.key = self.raw.key
        self.name = self.raw.name

class Path_(object):
    RE_ORIGIN = re.compile(r"(?:(?P<origin>[\w\-]+)?:)?(?P<path>\S+)$")
    RE_COMPONENT = re.compile(r'''
^
(?P<pname>[^[]+)
(\[(?P<key>[a-zA-Z0-9\-\/\.]+)
=
(?P<value>.*)
\])?$

''', re.VERBOSE)
    
    def __init__(self, path):
        self.raw = path

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

        names: List[str] = []
        elems: list = []
        
        path = path.strip()
        origin = None

        match = cls.RE_ORIGIN.search(path)
        origin = match.group("origin")
        path = match.group("path")
        
        if path:
            names = [re.sub(r"\\", "", name) for name in re.split(r"(?<!\\)/", path) if name]
        
        for name in names:
            match = cls.RE_COMPONENT.search(name)
            if not match:
                raise ValueError("path component parse error: %s" % name)

            if match.group("key") is not None:
                _key = {}
                for keyval in re.findall(r"\[([^]]*)\]", name):
                    val = keyval.split("=")[-1]
                    _key[keyval.split("=")[0]] = val

                pname = match.group("pname")
                elem = pb.PathElem(name=pname, key=_key) # type: ignore
                elems.append(elem)
            else:
                elems.append(pb.PathElem(name=name, key={})) # type: ignore
        
        return cls(pb.Path(origin=origin, elem=elems)) # type: ignore
