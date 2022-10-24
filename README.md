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
Usage: gnmipy [OPTIONS] COMMAND [ARGS]...

Options:
  --debug-grpc             enable grpc debugging
  --host-override TEXT     override grpc server hostname
  --insecure               use an insecure grpc chaneel
  -p, --password TEXT      password for basic authentication
  -t, --target TARGETTYPE  gnmi server hostaddr and port (<hostaddr>:<port>)
                           [1<=x<=65535]
  --tls-ca FILENAME        path to ca file
  --tls-cert FILENAME      path to cert file
  --tls-key FILENAME       path to key file
  -u, --username TEXT
  -c, --config PATH
  --help                   Show this message and exit.

Commands:
  capabilities
  get
  subscribe     subscribe to a gnmi path
  update
  version
```


### Examples


#### Command-line

```bash
gnmipy -u admin veos1:6030 subscribe /interfaces

# using jq to filter results
gimpy -u admin veos1:6030 subscribe /system | \
  jq '{time: .time, path: (.prefix + .updates[].path), value: .updates[].value}'
```


## API

```python
from gnmi.structures import SubscribeOptions
from gnmi import capabilites, get, delete, replace, update, subscribe
from gnmi.exceptions import GrpcDeadlineExceeded

paths = ["/system"]
target = "veos:6030"

for notif in get(target, paths, auth=("admin", "")):
    prefix = notif.prefix
    for update in notif.updates:
        print(f"{prefix + update.path} = {update.get_value()}")
    for delete in notif.deletes:
        print(f"{prefix + delete} = DELETED")

for notif in subscribe(target, paths, auth=("admin", ""),
                       options=SubscribeOptions(mode="once")):
    prefix = notif.prefix
    for update in notif.updates:
        print(f"{prefix + update.path} = {update.get_value()}")
    for delete in notif.deletes:
        print(f"{prefix + delete} = __DELETED__")
```
