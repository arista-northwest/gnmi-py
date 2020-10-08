
import pytest
import time
import json
import gnmi.proto.gnmi_pb2 as pb
from google.protobuf import any_pb2
from gnmi.util import escape_string, extract_value
from gnmi.messages import Path_, Update_

@pytest.fixture()
def gnmi_path():
    return pb.Path(origin=None, target=None, elem=[
        pb.PathElem(name="path"),
        pb.PathElem(name="to"),
        pb.PathElem(name="thing", key={"a": "apple"})
    ])

@pytest.fixture()
def gnmi_capability_response():
    return pb.CapabilityResponse(
        supported_models=[
            pb.ModelData(
                name="dummy-model", organization="Arita Inc.", version="1.0")
        ],
        supported_encodings=[0,3,4],
        gNMI_version="1.0"
    )

any_ = any_pb2.Any()
any_.Pack(pb.TypedValue(string_val="testany"))

@pytest.fixture(params=[
    ("any_val", any_),
    ("ascii_val", "ascii string"),
    ("bool_val", True),
    ("bytes_val", b"some bytes"),
    ("decimal_val", pb.Decimal64(digits=10, precision=2)),
    ("float_val", 3.14),
    ("int_val", -11),
    ("json_ietf_val", json.dumps({'a': 1, 'b': 2}).encode()),
    ("json_val", json.dumps("{'c': 3, 'd': 4}").encode()),
    ("leaflist_val", pb.ScalarArray(element=[
        pb.TypedValue(string_val="test"),
        pb.TypedValue(bool_val=False),
        pb.TypedValue(json_val=json.dumps("{'e': 5, 'f': 6}").encode())
    ])),
    ("proto_bytes", b"proto bytes?"),
    ("string_val", "string string"),
    ("uint_val", 21342342534)
])
def gnmi_tval(request):
    gtype, value = request.param
    return pb.TypedValue(**{gtype: value})

@pytest.fixture()
def gnmi_update(gnmi_path, gnmi_tval):
    return pb.Update(
        path=gnmi_path,
        val=gnmi_tval,
        duplicates=0
    )

@pytest.fixture()
def gnmi_notification(gnmi_update, gnmi_path):
    return pb.Notification(
        timestamp=int(time.time()) * 1000000000,
        prefix=None,
        update=[gnmi_update]
    )


def test_escape_string():
    str_ = r"[key=et/1/1]"
    assert escape_string(str_, "/[]=") == r"\[key\=et\/1\/1\]"

def test_extract_value_invalid(gnmi_path):
    with pytest.raises(ValueError):
        extract_value(None)

    # class _InvalidValue(object):

    #     def HasField(self, type_):
    #         return False

    # upd = pb.Update(
    #     path=gnmi_path,
    #     val=_InvalidValue,
    #     duplicates=0
    # )

    # with pytest.raises(ValueError):
    #     extract_value(upd)

def test_extract_value(gnmi_update):
    assert extract_value(gnmi_update)

def test_gnmi_path():
    paths = [
        "/system/nsftuff",
        "origin:/some/other/path",
        "/path/with/some[key=val-ue]/more[key=ssss]"
    ]
    for path in paths:
        pobj = Path_.from_string(path)
        pstr = pobj.to_string()

        [(e.name, e.key) for e in pobj.elements]

        assert path == pstr


def test_gnmi_update_fromkeyval():
    upd = Update_.from_keyval(("/path/to/val", "hello"))

    assert isinstance(upd, Update_)