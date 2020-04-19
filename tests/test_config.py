from gnmi.config import Config
from pprint import pprint
GNMI_CONFIG_FILE = "./examples/subscription.yml"

CONFIG_DATA = """
---
metadata:
    username: admin
    password: ""

get:
    options:
        prefix: /system/processes
        encoding: json
        type: all
    paths:
        - /system/config/hostname
        - /process[pid=*]/state
"""

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