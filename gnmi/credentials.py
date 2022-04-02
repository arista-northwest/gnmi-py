# -*- coding: utf-8 -*-
# Copyright (c) 2021 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

try:
    import keyring
except ImportError:
    pass

from typing import Optional
from dataclasses import dataclass
from collections import abc

@dataclass
class BaseCredentials(): ...

@dataclass
class SSLCredentials(BaseCredentials):
    root_certificates: bytes
    certificate_chain: bytes
    private_key: bytes

@dataclass
class UserPassCredentials(BaseCredentials):
    username: str
    password: str