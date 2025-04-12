from gnmi.target import Target

# >>> urlparse("unix:///var/run/gnmiServer.sock")
# ParseResult(scheme='unix', netloc='', path='/var/run/gnmiServer.sock', params='', query='', fragment='')
# >>> urlparse("http://172.0.0.1:6030")
# ParseResult(scheme='http', netloc='172.0.0.1:6030', path='', params='', query='', fragment='')
    

# def test_parse_unix():
#     want = "unix:///var/run/gnmiServer.sock"
#     tgt = Target.from_url(want)
#     print(tgt.parts())
#     assert str(tgt) == want

# def test_parse_http():
#     want = "http://172.0.0.1:6030"
#     tgt = Target.from_url(want)
#     print(tgt.parts())
#     assert str(tgt) == want

# def test_parse_naked():
#     want = "172.0.0.1:6030"
#     tgt = Target.from_url(want)
#     print(tgt.parts())
#     assert str(tgt) == want

def test_parse():
    tests = [
        ("unix:///var/run/gnmiServer.sock", "unix:///var/run/gnmiServer.sock"),
        ("/var/run/gnmiServer.sock", "unix:///var/run/gnmiServer.sock"),
        ("http://172.12.34.1:6030", "http://172.12.34.1:6030"),
        ("https://172.34.34.1:6030", "https://172.34.34.1:6030"),
        ("172.0.0.1:6030", "172.0.0.1:6030"),
        ("hostname:6030", "hostname:6030")
    ]

    for url, want in tests:
        tgt = Target.from_url(url)
        #print(str(tgt), want)
        assert str(tgt) == want