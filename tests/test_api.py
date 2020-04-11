
import os

import pytest

from gnmi.messages import CapabilitiesResponse_, GetResponse_
from gnmi.exceptions import GrpcDeadlineExceeded
from gnmi import capabilites, get, delete, replace, update, subscribe

GNMI_TARGET = os.environ.get("GNMI_TARGET", "veos3:6030")
GNMI_USER = os.environ.get("GNMI_USER", "admin")
GNMI_PASS = os.environ.get("GNMI_PASS", "")
GNMI_AUTH = (GNMI_USER, GNMI_PASS)


def test_discover():
    response = capabilites(GNMI_TARGET, auth=GNMI_AUTH)

    assert isinstance(response, CapabilitiesResponse_), "Invalid response"

def test_get():
    gen = get(GNMI_TARGET, paths=["/system/config/hostname"], auth=GNMI_AUTH)

    for resp in gen:
        path, value = resp
        assert path == "/system/config/hostname"
        assert isinstance(value, str)

seen = {}
def test_subscribe():
    gen = subscribe(GNMI_TARGET, paths=["/system/processes/process", "/interfaces/interface"], auth=GNMI_AUTH, options={"timeout": 2})
    for resp in gen:
        path, _ = resp
        if path.startswith("/system/processes/process"): 
            seen["/system/processes/process"] = True

        if path.startswith("/interfaces/interface"):
            seen["/interfaces/interface"] = True

    assert "/system/processes/process" in seen.keys()
    assert "/interfaces/interface" in seen.keys()

def test_set():
    path = "/system/config/hostname"
    hostname_ = None
    gen = get(GNMI_TARGET, [path], auth=GNMI_AUTH)
    for resp in gen:
        path, value = resp
        hostname_ = value

    updates = [
        ("/system/config/hostname", "minemeow")
    ]
    gen = update(GNMI_TARGET, updates=updates, auth=GNMI_AUTH)
    for r in gen:
        pass

    replacements = [
        ("/system/config", {"hostname": hostname_})
    ]
    gen = replace(GNMI_TARGET, replacements=replacements, auth=GNMI_AUTH)
    for r in gen:
        pass