import pytest

import gnmi.environments
from gnmi.config import Config
from gnmi.util import load_rc

YAML_SUPPORTED=False
try:
    import yaml
    YAML_SUPPORTED=True
except:
    ImportError

GNMI_CONFIG_FILE = "./examples/subscription.yaml"

CONFIG_DATA = """
metadata:
    username = "admin"
    password = ""

get:
    paths:
        - "/process[pid=*]/state"

    options:
    prefix: "/system/processes"
    type: "all"
"""

gnmi.environments.GNMI_RC_PATH = "./examples"

@pytest.mark.skipif(not YAML_SUPPORTED, reason="yaml module missing")
def test_load_rc():
    rc = load_rc()
    d = rc.dump()
    #pprint(d)

@pytest.mark.skipif(not YAML_SUPPORTED,  reason="yaml module missing")
def test_config_load():
    conf = Config.load_file(GNMI_CONFIG_FILE)

    assert isinstance(conf, Config), "Loaded did not return a Config object"

@pytest.mark.skipif(not YAML_SUPPORTED,  reason="yaml module missing")
def test_construct():
    conf = Config.load(CONFIG_DATA)
    assert isinstance(conf, Config), "Loaded did not return a Config object"

@pytest.mark.skipif(not YAML_SUPPORTED,  reason="yaml module missing")
def test_iter():
    
    conf = Config.load(CONFIG_DATA)

    for path in conf["get"].paths:
        assert path in ("/system/config/hostname", "/process[pid=*]/state")

@pytest.mark.skipif(not YAML_SUPPORTED,  reason="yaml module missing")
def test_len():
    conf = Config.load(CONFIG_DATA)
    len(conf)

@pytest.mark.skipif(not YAML_SUPPORTED,  reason="yaml module missing")
def test_dump():
    conf = Config.load(CONFIG_DATA)
    #print(conf)
    d = conf.dump()
    #pprint(d)

@pytest.mark.skipif(not YAML_SUPPORTED,  reason="yaml module missing")
def test_merge():
    rc = load_rc()
    conf = Config.load(CONFIG_DATA)
    #pprint(conf.merge(rc))