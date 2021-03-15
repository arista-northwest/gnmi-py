# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from gnmi.exceptions import GrpcDeadlineExceeded
from typing import Any, List, Tuple

from gnmi.session import Session
from gnmi.structures import Auth, CertificateStore, GetOptions, Metadata
from gnmi.structures import Options, SubscribeOptions, Target, GrpcOptions


__all__ = ["capabilites", "delete", "get", "replace", "subscribe", "update"]


def _new_session(hostaddr: str,
        auth: Auth = None,
        secure: bool = False,
        certificates: CertificateStore = {},
        override: str = None):
    
    host, port = hostaddr.split(":")
    target: Target = (host, int(port))

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
                secure=secure, grpc_options=grpc_options)


def capabilites(hostaddr: str, 
        auth: Auth = None,
        secure: bool = False,
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
    sess = _new_session(hostaddr, auth, secure, certificates, override)
    return sess.capabilities()


def get(hostaddr: str,
        paths: list,
        auth: Auth = None,
        secure: bool = False,
        certificates: CertificateStore = {},
        override: str = None,
        options: GetOptions = {}):
    """
    Get path(s) from target

    Usage::

        >>> get("veos1:6030", ["/system/config"],
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
    :param options: Get options
    :type options: gnmi.structures.GetOptions
    """
    sess = _new_session(hostaddr, auth, secure, certificates, override)
    
    responses = sess.get(paths, options=options)
    for notif in responses:
        prefix = notif.prefix
        for update in notif:
            path = prefix + update.path
            yield (str(path), update.get_value())


def subscribe(hostaddr: str,
        paths: list,
        auth: Auth = None,
        secure: bool = False,
        certificates: CertificateStore = {},
        override: str = None,
        options: SubscribeOptions = {}):
    """
    Subscribe to updates from target

    Usage::

        >>> responses = subscribe("veos1:6030", ["/system/processes/process"],
        ...     auth=("admin", "p4ssw0rd"))s
        ...
        >>> for path, val in responses:
        ...     print(path, val)

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
    sess = _new_session(hostaddr, auth, secure, certificates, override)

    try:
        for resp in sess.subscribe(paths, options=options):
            prefix = resp.update.prefix
            for update in resp.update.updates:
                path = prefix + update.path
                yield (str(path), update.get_value())
    except GrpcDeadlineExceeded:
        pass


def delete(hostaddr: str,
        deletes: List[str] = [],
        auth: Auth = None,
        secure: bool = False,
        certificates: CertificateStore = {},
        override: str = None,
        options: Options = {}):
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
    sess = _new_session(hostaddr, auth, secure, certificates, override)
    return sess.set(deletes=deletes, options=options)


def replace(hostaddr: str,
        replacements: List[Tuple[str, Any]] = [],
        auth: Auth = None,
        secure: bool = False,
        certificates: CertificateStore = {},
        override: str = None,
        options: Options = {}):
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
    sess = _new_session(hostaddr, auth, secure, certificates, override)
    return sess.set(replacements=replacements, options=options)


def update(hostaddr: str,
        updates: List[Tuple[str, Any]] = [],
        auth: Auth = None,
        secure: bool = False,
        certificates: CertificateStore = {},
        override: str = None,
        options: Options = {}):
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
    sess = _new_session(hostaddr, auth, secure, certificates, override)
    return sess.set(updates=updates, options=options)
