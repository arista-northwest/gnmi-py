# -*- coding: utf-8 -*-
# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from collections.abc import Mapping
from typing import Any

YAML_SUPPORTED: bool = False

try:
    import yaml
    YAML_SUPPORTED = True
except ImportError:
    pass

#TOML_SUPPORTED: bool = False
# try:
#     import toml
# except ImportError:
#     pass

class ConfigElem(Mapping):

    def __init__(self, data: dict):
        self.raw = data
        self._data = dict(ConfigElem._loader(k, v) for k, v in data.items())

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, name: str) -> Any:
        if name in self._data:
            return self._data[name]
    
    def __getattr__(self, name: str) -> Any:
        return self[name]
    
    def dump(self):
        data = {}
        for key, elem in self._data.items():
            if isinstance(elem, ConfigElem):
                elem = elem.dump()
            data[key] = elem
        return data

    def merge(self, other):
        if isinstance(other, ConfigElem):
            other = other.dump()
        this = self.dump()
        
        def _merge(a, b):
            
            for (key, value) in b.items():
                if isinstance(value, dict):
                    # get node or create one
                    node = a.setdefault(key, {})
                    _merge(node, value)
                elif isinstance(value, (tuple, list)):
                    if key not in a:
                        a[key] = []
                    a[key] += value
                else:
                    a[key] = value

        _merge(this, other)

        return Config(this)
        

    
    @classmethod
    def _loader(cls, name, value):

        if isinstance(value, dict):
            return name, cls(value)
        elif isinstance(value, (list, tuple)):
            nval = []
            for item in value:
                if isinstance(item, dict):
                    nval.append(cls(item))
                else:
                    nval.append(item)
            return name, nval
        else:
            return name, value

class Config(ConfigElem):
    
    @classmethod
    def load_file(cls, file):
        # if not YAML_SUPPORTED:
        #     raise ValueError("pyyaml module missing")
        with open(file, "r") as fh:
            data = cls.load(fh.read())
        return data
    
    @classmethod
    def load(cls, data: str):
        if not YAML_SUPPORTED:
            raise ValueError("pyyaml module missing")

        return cls(yaml.safe_load(data))