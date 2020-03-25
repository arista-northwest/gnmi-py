# gNMI Python Client


### Python 3

```
pip3 install -r requirements.txt
```

### Python 2

```
pip install -r py2.txt
```


### Usage

```
% python3 gnmi.py --help
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


#### openconfig paths...

```
python3 gnmi.py veos1:6030 /interfaces
```


#### Terminattr paths

```
python3 gnmi.py --origin eos_native veos3:6030 /Smash
```

