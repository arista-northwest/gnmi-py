# -*- coding: utf-8 -*-
# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

class GrpcError(Exception):
    def __init__(self, status):
        super(GrpcError, self).__init__("%s: %s" %
                                        (status.code, status.details))

class GrpcDeadlineExceeded(GrpcError): ...

class GnmiDeprecationError(Exception): ...
