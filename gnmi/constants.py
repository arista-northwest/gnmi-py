# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from typing import List
from typing_extensions import Final

DEFAULT_GRPC_PORT = 6030
DEFAULT_GRPC_HOST = "localhost"

MODE_MAP: Final[List[str]] = [
    "stream",
    "once",
    "poll"
]

DATA_TYPE_MAP: Final[List[str]] = [
    "all",
    "config",
    "state",
    "operational"
]