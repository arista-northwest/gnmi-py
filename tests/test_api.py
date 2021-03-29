# -*- coding: utf-8 -*-
# Copyright (c) 2021 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import os
from functools import partial
import pytest

from gnmi.messages import CapabilitiesResponse_, GetResponse_, Path_, Update_
from gnmi.exceptions import GrpcDeadlineExceeded
from gnmi import capabilites, get, delete, replace, update, subscribe

from tests.conftest import GNMI_AUTH, GNMI_TARGET, GNMI_SECURE, certificates, is_secure
from tests.conftest import GNMI_CERT_CHAIN, GNMI_PRIVAE_KEY, GNMI_ROOT_CERT 

pytestmark = pytest.mark.skipif(not GNMI_TARGET, reason="gNMI target not set")


def test_discover(is_secure, certificates):
    response = capabilites(GNMI_TARGET,
        secure=is_secure, certificates=certificates, auth=GNMI_AUTH)

    assert isinstance(response, CapabilitiesResponse_), "Invalid response"

def test_get(is_secure, certificates):

    resp = get(GNMI_TARGET, paths=["/system/config/hostname"],
        secure=is_secure, certificates=certificates, auth=GNMI_AUTH)

    for notif in resp:
        for update in notif.update:
            assert str(update.path) == "/system/config/hostname"
            assert isinstance(update.get_value(), str)

def test_subscribe(is_secure, certificates):
    resp = subscribe(GNMI_TARGET,
        paths=["/system/processes/process", "/interfaces/interface"],
        secure=is_secure, certificates=certificates, auth=GNMI_AUTH,
        options={"timeout": 2})
    
    seen = {}
    for notif in resp:
        for u in notif:
            if isinstance(u, Update_):
                path = str(u.path)
                if path.startswith("/system/processes/process"): 
                    seen["/system/processes/process"] = True

                if path.startswith("/interfaces/interface"):
                    seen["/interfaces/interface"] = True

            elif isinstance(u, Path_):
                print(f"DELETED: {path}")

    assert "/system/processes/process" in seen.keys()
    assert "/interfaces/interface" in seen.keys()


def test_set(is_secure, certificates, request):
     
    path = "/system/config/hostname"
    
    def _get_hostname():
        resp = get(GNMI_TARGET, ["/system/config/hostname"], secure=is_secure,
            certificates=certificates, auth=GNMI_AUTH)
        for notif in resp:
            for update in notif:
                return update.get_value()
    
    hostname = _get_hostname()
    
    def _rollback():
        hostname_ = _get_hostname()
        if hostname_ != hostname:
            update(GNMI_TARGET, updates=[("/system/config/hostname", hostname)],
                secure=is_secure, certificates=certificates, auth=GNMI_AUTH)
    
    request.addfinalizer(_rollback)
        
    updates = [
        ("/system/config/hostname", "minemeow")
    ]
    gen = update(GNMI_TARGET, updates=updates,
        secure=is_secure, certificates=certificates, auth=GNMI_AUTH)
    for r in gen:
        pass

    replacements = [
        ("/system/config", {"hostname": hostname})
    ]
    gen = replace(GNMI_TARGET, replacements=replacements,
        secure=is_secure, certificates=certificates, auth=GNMI_AUTH)

    for r in gen:
        pass