#!/usr/bin/env bash
# echo "Updating gNMI amd gRPC sub-modules..."
# git submodule add https://github.com/openconfig/gnmi.git submodule/openconfig
# git submodule add https://github.com/grpc/grpc.git submodule/grpc
# git submodule update --remote
# SUBMODULE_DIR=submodule

set -x
set -e

WORKDIR=build/proto

mkdir -p ${WORKDIR}

# Downloading protos
wget https://raw.githubusercontent.com/openconfig/gnmi/master/proto/gnmi/gnmi.proto -O ${WORKDIR}/gnmi.proto
wget https://raw.githubusercontent.com/openconfig/gnmi/master/proto/gnmi_ext/gnmi_ext.proto -O ${WORKDIR}/gnmi_ext.proto
wget https://raw.githubusercontent.com/grpc/grpc/master/src/proto/grpc/status/status.proto -O ${WORKDIR}/status.proto

echo "Fixing proto imports..."
sed -i '' 's/github.com\/openconfig\/gnmi\/proto\/gnmi_ext\///g' ${WORKDIR}/gnmi.proto

echo "Generating python modules..."
python3 -m grpc_tools.protoc \
  --proto_path=${WORKDIR} \
  --python_out=${WORKDIR} \
  --grpc_python_out=${WORKDIR} \
  gnmi.proto gnmi_ext.proto status.proto

echo "Fixing python imports..."
sed -i '' 's/import gnmi_pb2/from . import gnmi_pb2/' ${WORKDIR}/gnmi_pb2_grpc.py
sed -i '' 's/import gnmi_ext_pb2/from . import gnmi_ext_pb2/' ${WORKDIR}/gnmi_pb2.py

echo "Copying modules to project..."
cp ${WORKDIR}/*.py gnmi/proto/

echo "Cleaning up..."
rm ${WORKDIR}/*
rmdir ${WORKDIR}
