
import os
from functools import partial
import pytest

from gnmi.messages import CapabilitiesResponse_, GetResponse_, Update_
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

    gen = get(GNMI_TARGET, paths=["/system/config/hostname"],
        secure=is_secure, certificates=certificates, auth=GNMI_AUTH)

    for update in gen:
        #path, value = resp
        assert str(update.path) == "/system/config/hostname"
        assert isinstance(update, Update_)

def test_subscribe(is_secure, certificates):
    gen = subscribe(GNMI_TARGET,
        paths=["/system/processes/process", "/interfaces/interface"],
        secure=is_secure, certificates=certificates, auth=GNMI_AUTH,
        options={"timeout": 2})
    
    seen = {}
    for update in gen:
        path = str(update.path)
        if path.startswith("/system/processes/process"): 
            seen["/system/processes/process"] = True

        if path.startswith("/interfaces/interface"):
            seen["/interfaces/interface"] = True

    assert "/system/processes/process" in seen.keys()
    assert "/interfaces/interface" in seen.keys()


def test_set(is_secure, certificates, request):
    
    path = "/system/config/hostname"
    
    def _get_hostname():
        gen = get(GNMI_TARGET, ["/system/config/hostname"], secure=is_secure,
            certificates=certificates, auth=GNMI_AUTH)
        for update in gen:      
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