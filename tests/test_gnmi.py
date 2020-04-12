import os
import pytest
from tests.conftest import GNMI_TARGET, GNMI_SECURE
from gnmi.session import Session
from gnmi.messages import Path_, Update_
from gnmi.exceptions import GrpcError, GrpcDeadlineExceeded
from gnmi import util
from os import replace

GNMI_PATHS = os.environ.get("GNMI_PATHS", "/system/config;/system/memory/state")

@pytest.fixture()
def paths():
    return [Path_.from_string(p) for p in GNMI_PATHS.split(";")]

@pytest.fixture()
def target():
    host, port = GNMI_TARGET.split(":")[:2]

    return (host, int(port))

@pytest.fixture()
def session(target, certificates):
    metadata = [
        ("username", "admin"),
        ("password", "")
    ]
    if GNMI_SECURE:
        secure = True
    else:
        secure = False
    
    #print(certificates)
    return Session(target, secure=secure, certificates=certificates, metadata=metadata)

def test_cap(session):
    resp = session.capabilities()


def test_get(session, paths):
    resp = session.get(paths, options={})
    for notif in resp:
        assert notif.timestamp is not None
        for update in notif.updates:
            assert type(update) is Update_
            assert type(update.path) is Path_
            assert hasattr(update, "val")


def test_sub(session, paths):
    
    with pytest.raises(GrpcDeadlineExceeded) as exc:
        for resp in session.subscribe(paths, options={"timeout": 2}):
            prefix = resp.update.prefix
            for update in resp.update.updates:
                path = prefix + update.path
                #print(str(path), update.value)


def test_set(session):
    path = "/system/config/hostname"

    def _get_hostname():
        return session.get([path]).collect()[0][0].value

    hostname_ = _get_hostname()

    invalid = [
        ("/system/config/hostname", 1.1),
    ]

    with pytest.raises(GrpcError) as err:
        rsps = session.set(replacements=invalid)
    
    #assert rsps.collect()[0].op == "INVALID"

    replacements = [
        ("/system/config/hostname", "minemeow"),
    ]
    
    rsps = session.set(replacements=replacements)
    assert rsps.collect()[0].op == "REPLACE"

    _ = session.get(["/system/config/hostname"])

    assert _get_hostname() == "minemeow"

    updates = [
        ("/system/config", {"hostname": hostname_})
    ]

    rsps = session.set(updates=updates)
    assert rsps.collect()[0].op == "UPDATE"

    assert _get_hostname() == hostname_

    # deletes = [

    # ]
    # rsps = session.set(deletes=updates)