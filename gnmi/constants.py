# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from typing import List
from typing_extensions import Final

import grpc

DEFAULT_GRPC_PORT: Final[int] = 6030
DEFAULT_GRPC_HOST: Final[str] = "localhost"

GNMIRC_FILES: Final[List[str]] =  [".gnmirc", "_gnmirc"]

GRPC_CODE_MAP: Final[dict] = {x.value[0]: x for x in grpc.StatusCode}

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