
from gnmi.messages import Path_, Update_

def test_gnmi_path():
    paths = [
        "/system/nsftuff",
        "origin:/some/other/path",
        "/path/with/some[key=val-ue][df=sdf]/more[key=ssss]"
    ]
    for path in paths:
        pobj = Path_.from_string(path)
        pstr = pobj.to_string()

        print([(e.name, e.key) for e in pobj.elements])
        print(pstr)
        print(str(path))
        print(pobj.raw)

def test_gnmi_update():
    upd = Update_.from_keyval(("/path/to/val", "hello"))

    assert isinstance(upd, Update_)