# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import sys

__version__ = "0.5.4"

if sys.version_info < (3, 7):
    # see: https://devguide.python.org/devcycle/
    raise ValueError("Python 3.6+ is required")

from gnmi.session import Session
from gnmi.api import capabilites, delete, get, replace, subscribe, update
