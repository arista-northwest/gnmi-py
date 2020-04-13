# gNMI Python Client

## Installation

### Python 3

#### General Use

```bash
pip3 install gnmi-py
```

#### Development

```bash
git clone https://github.com/arista-northwest/gnmi-py.git
cd gnmi-py
pip3 install -r requirements.txt
python3 setup.py develop
```

### Python 2

Not supported :)


### Usage

```bash
% gnmipy --help
usage: gnmi.py [-h] [--version] [-u USERNAME] [-p PASSWORD]
               [--interval INTERVAL] [--timeout TIMEOUT]
               [--heartbeat HEARTBEAT] [--aggregate] [--suppress]
               [--submode SUBMODE] [--mode MODE] [--encoding ENCODING]
               [--qos QOS] [--use-alias] [--prefix PREFIX]
               target [paths [paths ...]]

positional arguments:
  target                gNMI gRPC server (default: localhost:6030)
  paths

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit

  -u USERNAME, --username USERNAME
  -p PASSWORD, --password PASSWORD

  --interval INTERVAL   sample interval (default: 10s)
  --timeout TIMEOUT     subscription duration in seconds (default: none)
  --heartbeat HEARTBEAT
                        heartbeat interval (default: none)
  --aggregate           allow aggregation
  --suppress            suppress redundant
  --submode SUBMODE     subscription mode [target-defined, on-change, sample]
  --mode MODE           [stream, once, poll]
  --encoding ENCODING   [json, bytes, proto, ascii, json-ietf]
  --qos QOS             [JSON, BYTES, PROTO, ASCII, JSON_IETF]
  --use-alias           use alias
  --prefix PREFIX       gRPC path prefix (default: none)
```


### Examples


#### Command-line

```basha
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
        print(path, update.value)

paths = ["/system/processes/process"]
try:
    for resp in sess.subscribe(paths, options={"timeout": 5}):
        prefix = resp.update.prefix
        for update in resp.update.updates:
            path = prefix + update.path
            print(str(path), update.value)
except GrpcDeadlineExceeded:
    print("User defined timeout exceeded.")
