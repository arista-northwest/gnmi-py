#!/usr/bin/env python3

from gnmi.structures import SubscribeOptions
from gnmi import get, delete, update, subscribe

paths = ["/system"]
target = "192.168.56.103:50010"

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