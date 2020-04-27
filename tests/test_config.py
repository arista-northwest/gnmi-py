import os

import gnmi.environments
from gnmi.config import Config
from gnmi.util import load_rc
from pprint import pprint

GNMI_CONFIG_FILE = "./examples/subscription.toml"

CONFIG_DATA = """
[metadata]
username = "admin"
password = ""

[get]
paths = ["/process[pid=*]/state"]

[get.options]
prefix = "/system/processes"
type = "all"
"""

gnmi.environments.RC_PATH = "./examples"

def test_load_rc():
    rc = load_rc()
    d = rc.dump()
    pprint(d)

def test_config_load():
    conf = Config.load(GNMI_CONFIG_FILE)

    assert isinstance(conf, Config), "Loaded did not return a Config object"

def test_construct():
    conf = Config.loads(CONFIG_DATA)
    assert isinstance(conf, Config), "Loaded did not return a Config object"

def test_iter():
    
    conf = Config.loads(CONFIG_DATA)

    for path in conf["get"].paths:
        assert path in ("/system/config/hostname", "/process[pid=*]/state")

def test_len():
    conf = Config.loads(CONFIG_DATA)
    len(conf)


def test_dump():
    conf = Config.loads(CONFIG_DATA)
    print(conf)
    d = conf.dump()
    pprint(d)

def test_merge():
    rc = load_rc()
    conf = Config.loads(CONFIG_DATA)
    pprint(conf.merge(rc))