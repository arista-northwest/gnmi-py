

from gnmi import util

def test_path_join():
    elems = ["/", "/test/path[key=val-ue]/", "end/of/test/path/"]
    assert util.path_join(*elems) == "/test/path[key=val-ue]/end/of/test/path"
