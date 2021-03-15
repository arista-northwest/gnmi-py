# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import os
import pathlib

_HOME = pathlib.Path.home()

GNMI_RC_PATH = os.environ.get("RC_PATH", _HOME)
GNMI_NO_DEPRECATED = True if os.environ.get("GNMI_NO_DEPRECATED") else False