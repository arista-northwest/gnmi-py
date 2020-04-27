
from gnmi import util

# def test_load_rc():
#     rc = util.load_rc()
    
#     assert rc["metadata"]

#     if "certificates" in rc:
#         for k, v in rc["certificates"].items():
#             assert k in ("certificat_chain", "private_key", "root_certificates")
    
#     if "get" in rc:
#         assert rc["get"]["options"]["encoding"]

#     if "subscribe" in rc:
#         assert rc["subscribe"]
#         assert rc["subscribe"]["options"]["timeout"]


def test_parse_path():
    parsed = util.parse_path(r"/apple/be\/d[cat=yes][dog=no]/fowl/grub")
    
    assert parsed[0]["name"] == "apple"
    assert parsed[1]["keys"]["cat"] == "yes"
    assert parsed[1]["keys"]["dog"] == "no"