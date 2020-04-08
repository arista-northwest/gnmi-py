import os
import pytest
from gnmi.session import Session
from gnmi.messages import Path_, Update_
from gnmi.exceptions import GrpcError, GrpcDeadlineExceeded
from gnmi import util

GNMI_TARGET = os.environ.get("GNMI_TARGET", "veos3:6030")
GNMI_PATHS = os.environ.get("GNMI_PATHS", "/system/config;/system/memory/state")


@pytest.fixture()
def gnmi_paths():
    return GNMI_PATHS.split(";")

@pytest.fixture()
def gnmi_target():
    host, port = GNMI_TARGET.split(":")[:2]

    return (host, int(port))

@pytest.fixture()
def gnmi_session(gnmi_target):
    metadata = [
        ("username", "admin"),
        ("password", "")
    ]
    return Session(gnmi_target, metadata=metadata)

def test_gnmi_path(gnmi_paths):
    for path in gnmi_paths + ["/path/with/some[key=val-ue][df=sdf]/more[key=ssss]"]:
        pobj = Path_.from_string(path)
        pstr = pobj.to_string()

        _ = [(e.name, e.key) for e in pobj.elements]
        _ = pstr

def test_gnmi_cap(gnmi_session):
    resp = gnmi_session.capabilities()
    print(resp)

def test_gnmi_get(gnmi_session, gnmi_paths):
    resp = gnmi_session.get(gnmi_paths)
    for notif in resp.notifications:
        assert notif.timestamp is not None
        for update in notif.updates:
            assert type(update) is Update_
            assert type(update.path) is Path_
            assert hasattr(update, "val")


def test_gnmi_sub(gnmi_session, gnmi_paths):
    
    with pytest.raises(GrpcDeadlineExceeded) as exc:
        for resp in gnmi_session.subscribe(gnmi_paths, options={"timeout": 2}):
            prefix = resp.update.prefix
            for update in resp.update.updates:
                path = prefix + update.path
                print(str(path), update.value)