# -*- coding: utf-8 -*-
# Copyright (c) 2025 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from gnmi.proto.gnmi_pb2 import Path
from gnmi.messages import Notification_, SetResponse_, Update_, Path_
from gnmi.exceptions import GrpcDeadlineExceeded
from typing import Any, Generator, List, Tuple

from gnmi.session import Session
from gnmi.structures import Auth, CertificateStore, GetOptions, Metadata
from gnmi.structures import Options, SubscribeOptions, GrpcOptions
from gnmi.target import Target

__all__ = ["capabilites", "delete", "get", "replace", "subscribe", "update"]

def _new_session(target: str,
        auth: Auth = None,
        insecure: bool = False,
        certificates: CertificateStore = {},
        override: str = None):
    
    target = Target.from_url(target)

    metadata: Metadata = {}
    if auth:
        username, password = auth
        metadata = {
            "username": username,
            "password": password
        }
    
    grpc_options: GrpcOptions = {}
    if override:
        grpc_options["server_host_override"] = override
    
    return Session(target, metadata=metadata, certificates=certificates,
                insecure=insecure, grpc_options=grpc_options)


def capabilites(target: str, 
        auth: Auth = None,
        insecure: bool = False,
        certificates: CertificateStore = {},
        override: str = None):
    """
    Get supported models and encodings from target

    Usage::

        >>> capabilites("veos1:6030", auth=("admin", "p4ssw0rd"))

    :param target: gNMI target
    :type target: str
    :param auth: username and password
    :type auth: tuple
    :param certificates: SSL certificates
    :type auth: gnmi.structures.CertificateStore
    :param override: override hostname
    :type override: str
    """
    sess = _new_session(target, auth, insecure, certificates, override)
    return sess.capabilities()


def get(target: str,
        paths: list,
        auth: Auth = None,
        insecure: bool = False,
        certificates: CertificateStore = {},
        override: str = None,
        options: GetOptions = {}) -> Generator[Notification_, None, None]:
    """
    Get path(s) from target

    Usage::

        >>> respones = get("veos1:6030", ["/system/config"],
        ...     auth=("admin", "p4ssw0rd"))
        >>> for notif in respones:
        ...     for update in notif.updates:
        ...         print(update.path, update.get_value())
        ...     for path in notif.deletes:
        ...         print(str(path)) 

    :param target: gNMI target
    :type target: str
    :param paths: Path string
    :type paths: str
    :param auth: username and password
    :type auth: tuple
    :param certificates: SSL certificates
    :type certificates: gnmi.structures.CertificateStore
    :param override: override hostname
    :type override: str
    :param options: Get options
    :type options: gnmi.structures.GetOptions
    """
    sess = _new_session(target, auth, insecure, certificates, override)

    for notif in sess.get(paths, options=options):
        yield notif


def subscribe(target: str,
        paths: list,
        auth: Auth = None,
        insecure: bool = False,
        certificates: CertificateStore = {},
        override: str = None,
        options: SubscribeOptions = {}) -> Generator[Notification_, None, None]:
    """
    Subscribe to updates from target

    Usage::

        >>> responses = subscribe("veos1:6030", ["/system/processes/process"],
        ...     auth=("admin", "p4ssw0rd"))s
        ...
        >>> for resp in responses:
        ...     for update in resp.update:
        ...         for update in update.updates:
        ...             print(update.path, update.get_value())
        ...         for path in update.deletes:
        ...             print(str(path))  

    :param target: gNMI target
    :type target: str
    :param paths: Path string
    :type paths: str
    :param auth: username and password
    :type auth: tuple
    :param certificates: SSL certificates
    :type certificates: gnmi.structures.CertificateStore
    :param override: override hostname
    :type override: str
    :param options: Subscribe options
    :type options: gnmi.structures.SubscribeOptions
    """
    sess = _new_session(target, auth, insecure, certificates, override)

    try:
        for resp in sess.subscribe(paths, options=options):
            if resp.sync_response:
                continue
            yield resp.update

    except GrpcDeadlineExceeded:
        pass


def delete(target: str,
        deletes: List[str] = [],
        auth: Auth = None,
        insecure: bool = False,
        certificates: CertificateStore = {},
        override: str = None,
        options: Options = {}) -> SetResponse_:
    """
    Delete paths from the target

    Usage::

        >>> delete("veos1:6030", ["/some/deletable/path"],
        ...     auth=("admin", "p4ssw0rd"))

    :param target: gNMI target
    :type target: str
    :param paths: Path string
    :type paths: str
    :param auth: username and password
    :type auth: tuple
    :param certificates: SSL certificates
    :type certificates: gnmi.structures.CertificateStore
    :param override: override hostname
    :type override: str
    :param options: Subscribe options
    :type options: gnmi.structures.SubscribeOptions
    """
    sess = _new_session(target, auth, insecure, certificates, override)
    return sess.set(deletes=deletes, options=options)


def replace(target: str,
        replacements: List[Tuple[str, Any]] = [],
        auth: Auth = None,
        insecure: bool = False,
        certificates: CertificateStore = {},
        override: str = None,
        options: Options = {}) -> SetResponse_:
    """
    Replace paths on the target

    Usage::
        >>> replacements = [("/system/config/hostname", "newhostname")]
        >>> replace("veos1:6030", replacements,
        ...     auth=("admin", "p4ssw0rd"))

    :param target: gNMI target
    :type target: str
    :param replacements: update path, value
    :type replacements: tuple
    :param auth: username and password
    :type auth: tuple
    :param certificates: SSL certificates
    :type certificates: gnmi.structures.CertificateStore
    :param override: override hostname
    :type override: str
    :param options: Subscribe options
    :type options: gnmi.structures.SubscribeOptions
    """
    sess = _new_session(target, auth, insecure, certificates, override)
    return sess.set(replacements=replacements, options=options)


def update(target: str,
        updates: List[Tuple[str, Any]] = [],
        auth: Auth = None,
        insecure: bool = False,
        certificates: CertificateStore = {},
        override: str = None,
        options: Options = {}) -> SetResponse_:
    """
    Update paths on the target

    Usage::
        >>> updates = [("/system/config", {"hostname": "newhostname"})]
        >>> replace("veos1:6030", updates,
        ...     auth=("admin", "p4ssw0rd"))

    :param target: gNMI target
    :type target: str
    :param updates: update path, value
    :type updates: tuple
    :param auth: username and password
    :type auth: tuple
    :param certificates: SSL certificates
    :type certificates: gnmi.structures.CertificateStore
    :param override: override hostname
    :type override: str
    :param options: Subscribe options
    :type options: gnmi.structures.SubscribeOptions
    """
    sess = _new_session(target, auth, insecure, certificates, override)
    return sess.set(updates=updates, options=options)
