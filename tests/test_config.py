from gnmi.config import Config
from pprint import pprint
GNMI_CONFIG_FILE = "./examples/subscription.yml"

def test_config():
    conf = Config.load(GNMI_CONFIG_FILE)
    # d = dict(conf)  
    # print(d)
    print(conf["subscribe"], type(conf["subscribe"]))
    print(conf.subscribe.metadata)
    print(conf.subscribe.subscription_list.subscription[0].path)
    #pprint(dict(conf))