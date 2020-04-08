# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from typing import List, Optional, Tuple, Any
from typing_extensions import TypedDict

class CertificateStore(TypedDict):
    chain: str
    private_key: str
    root: Optional[str]


Auth = Tuple[str, Optional[str]]

Target = Tuple[str, Optional[int]]

Metadata = List[Tuple[str, Any]]


class Options(TypedDict, total=False):
    prefix: str
    encoding: str
    extension: list


class SubscribeOptions(Options, total=False):
    aggregate: bool
    heartbeat: Optional[int]
    interval: Optional[int]
    mode: str
    qos: int
    submode: str
    suppress: bool
    timeout: Optional[int]
    use_alias: bool


class GetOptions(Options, total=False):
    type: str
    use_models: list

