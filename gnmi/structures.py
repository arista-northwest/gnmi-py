# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from ssl import OP_ALL
from typing import List, Optional, Tuple, Any
from typing_extensions import TypedDict
from gnmi.messages import Path_

class CertificateStore(TypedDict, total=False):
    certificat_chain: bytes
    private_key: bytes
    root_certificates: bytes


Auth = Tuple[str, Optional[str]]

Target = Tuple[str, int]

Metadata = List[Tuple[str, Any]]


class Options(TypedDict, total=False):
    prefix: Any
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

class GrpcOptions(TypedDict, total=False):
    server_host_override: str
    
