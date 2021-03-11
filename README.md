# gNMI Python Client

## Installation

### Python 3

#### General Use

```bash
pip3 install gnmi-py
```

#### Development

```bash
git clone https://gitlab.aristanetworks.com/arista-northwest/gnmi-py.git
# installs pipenv and requirements
make init
pipenv shell
```

### Python 2

Not supported :)


### Usage

```
% gnmipy --help
usage: gnmipy [-h] [--version] [-c CONFIG] [-d] [-u USERNAME] [-p PASSWORD]
              [--encoding {json,bytes,proto,ascii,json-ietf}]
              [--prefix PREFIX] [--get-type {config,state,operational}]
              [--interval INTERVAL] [--timeout TIMEOUT]
              [--heartbeat HEARTBEAT] [--aggregate] [--suppress]
              [--mode {stream,once,poll}]
              [--submode {target-defined,on-change,sample}] [--once]
              [--qos QOS] [--use-alias]
              target {capabilities,get,subscribe} [paths [paths ...]]

positional arguments:
  target                gNMI gRPC server
  {capabilities,get,subscribe}
                        gNMI operation [capabilities, get, subscribe]
  paths

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -c CONFIG, --config CONFIG
                        Path to gNMI config file

  -d, --debug           enable gRPC debugging

  -u USERNAME, --username USERNAME
  -p PASSWORD, --password PASSWORD

Common options:
  --encoding {json,bytes,proto,ascii,json-ietf}
                        set encoding
  --prefix PREFIX       gRPC path prefix (default: <empty>)

Get options:
  --get-type {config,state,operational}

Subscribe options:
  --interval INTERVAL   sample interval in milliseconds (default: 10s)
  --timeout TIMEOUT     subscription duration in seconds (default: None)
  --heartbeat HEARTBEAT
                        heartbeat interval in milliseconds (default: None)
  --aggregate           allow aggregation
  --suppress            suppress redundant
  --mode {stream,once,poll}
                        Specify subscription mode
  --submode {target-defined,on-change,sample}
                        subscription sub-mode
  --once                End subscription after first sync_response. This is a
                        workaround for implementions that do not support
                        'once' subscription mode
  --qos QOS             DSCP value to be set on transmitted telemetry
  --use-alias           use aliases
```


### Examples


#### Command-line

```bash
gnmipy veos1:6030 subscribe /interfaces
```


## API

```python
from gnmi.session import Session
from gnmi.exceptions import GrpcDeadlineExceeded


metadata = [
    ("username", "admin"),
    ("password", "")
]


paths = ["/config", "/memory/state"]
target = ("veos", 6030)
sess = Session(target, metadata=metadata)


for notif in sess.get(paths, options={"prefix": "/system"}):
    prefix = notif.prefix
    for update in notif.updates:
        path = prefix + update.path
        print(path, update.get_value())

paths = ["/system/processes/process"]
try:
    for resp in sess.subscribe(paths, options={"timeout": 5}):
        prefix = resp.update.prefix
        for update in resp.update.updates:
            path = prefix + update.path
            print(str(path), update.get_value())
except GrpcDeadlineExceeded:
    print("User defined timeout exceeded.")
