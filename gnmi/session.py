# -*- coding: utf-8 -*-
# Copyright (c) 2020 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import grpc
import google.protobuf as _
from gnmi.proto import gnmi_pb2 as pb  # type: ignore
from gnmi.proto import gnmi_pb2_grpc  # type: ignore

from typing import Optional, Iterator

from gnmi import util
from gnmi.messages import CapabilitiesResponse_, GetResponse_, Path_, Status_
from gnmi.messages import SubscribeResponse_
from gnmi.structures import Metadata, Target, CertificateStore, Options
from gnmi.structures import GetOptions, SubscribeOptions
from gnmi.constants import DEFAULT_GRPC_PORT, MODE_MAP, DATA_TYPE_MAP
from gnmi.exceptions import GrpcError, GrpcDeadlineExceeded

class Session(object):

    def __init__(self,
                 target: Target,
                 metadata: Metadata = [],
                 certificates: CertificateStore = None,
                 host_override: str = ""):

        self._target = target
        self.metadata = metadata
        self._certificates = certificates
        self._host_override = host_override

        self._credentials = self._create_credentials()
        self._channel = self._create_channel()

        self._stub = gnmi_pb2_grpc.gNMIStub(self._channel)  # type: ignore

    @property
    def target(self) -> Target:
        _t: Target = (self._target[0], self._target[1] or DEFAULT_GRPC_PORT)
        return _t

    @property
    def addr(self):
        return "%s:%d" % self.target

    def _create_credentials(self):
        return []

    def _create_channel(self):
        return self._insecure_channel()

    def _insecure_channel(self):
        return grpc.insecure_channel(self.addr)  # type: ignore

    def capabilities(self, options: Options = {}) -> CapabilitiesResponse_:
        if options.get("extension"):
            raise ValueError("'extension' is not implemented yet.")

        _cr = pb.CapabilityRequest()  # type: ignore

        try:
            response = self._stub.Capabilities(_cr, metadata=self.metadata)  
        except grpc.RpcError as rpcerr:
            status = Status_.from_call(rpcerr)
            raise GrpcError(status)
        
        return CapabilitiesResponse_(response)

    def get(self, paths: list, options: GetOptions = {}) -> GetResponse_:
        response: Optional[GetResponse_] = None
        prefix = util.parse_path(options.get("prefix") or "/")
        encoding = util.get_gnmi_constant(options.get("encoding") or "json")
        type_ = DATA_TYPE_MAP.index(options.get("type") or "all")
        paths = [util.parse_path(path) for path in paths]

        _gr = pb.GetRequest(path=paths, prefix=prefix, encoding=encoding,
                            type=type_)  # type: ignore

        try:
            response = self._stub.Get(_gr, metadata=self.metadata)
        except grpc.RpcError as rpcerr:
            status = Status_.from_call(rpcerr)
            raise GrpcError(status)
        
        return GetResponse_(response)

    def set(self): ...

    def subscribe(self, paths: list, options: SubscribeOptions = {}) -> Iterator[SubscribeResponse_]:

        aggregate = options.get("aggregate", False)
        encoding = util.get_gnmi_constant(options.get("encoding", "json"))
        heartbeat = options.get("heartbeat", None)
        interval = options.get("interval", None)
        mode = MODE_MAP.index(options.get("mode", "stream"))
        prefix = Path_.from_string(options.get("prefix") or "/")
        qos = pb.QOSMarking(marking=options.get("qos", 0))
        submode = util.get_gnmi_constant(options.get("submode") or "on-change")
        suppress = options.get("suppress", False)
        timeout = options.get("timeout", None)
        use_alias = options.get("use_alias", False)

        paths = [Path_.from_string(path) for path in paths]

        subs = []
        for path in paths:
            sub = pb.Subscription(path=path.raw, mode=submode,
                                  suppress_redundant=suppress,
                                  sample_interval=interval,
                                  heartbeat_interval=heartbeat)
            subs.append(sub)

        def _sr():

            sub_list = pb.SubscriptionList(prefix=prefix.raw, mode=mode,
                                           allow_aggregation=aggregate,
                                           encoding=encoding, subscription=subs,
                                           use_aliases=use_alias, qos=qos)
            req_iter = pb.SubscribeRequest(subscribe=sub_list)
            yield req_iter

        try:
            responses = self._stub.Subscribe(
                _sr(), timeout, metadata=self.metadata)
            for response in responses:
                if response.HasField("sync_response"):
                    continue
                elif response.HasField("update"):
                    yield SubscribeResponse_(response)
                else:
                    raise ValueError("Unknown response: " + str(response))

        except grpc.RpcError as rpcerr:
            status = Status_.from_call(rpcerr)

            if status.code.name == "DEADLINE_EXCEEDED":
                raise GrpcDeadlineExceeded(status)
            else:
                raise GrpcError(status)
