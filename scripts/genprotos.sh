#!/usr/bin/env bash
echo "Updating gNMI sub-module..."
git submodule update --remote



WORKDIR=${TMPDIR}/proto

mkdir -p ${WORKDIR}

echo "Fixing proto imports..."
sed 's/github.com\/openconfig\/gnmi\/proto\/gnmi_ext\///g' \
  openconfig/gnmi/proto/gnmi/gnmi.proto > ${WORKDIR}/gnmi.proto

cp openconfig/gnmi/proto/gnmi_ext/gnmi_ext.proto ${WORKDIR}

echo "Generating python modules..."
python3 -m grpc_tools.protoc \
  --proto_path=${WORKDIR} \
  --python_out=${WORKDIR} \
  --grpc_python_out=${WORKDIR} \
  gnmi.proto gnmi_ext.proto

echo "Fixing python imports..."
sed -i .bak 's/import gnmi_pb2/from . import gnmi_pb2/' ${WORKDIR}/gnmi_pb2_grpc.py
sed -i .bak 's/import gnmi_ext_pb2/from . import gnmi_ext_pb2/' ${WORKDIR}/gnmi_pb2.py

echo "Copying modules to project..."
cp ${WORKDIR}/*.py gnmi/proto/

echo "Cleaning up..."
rm ${WORKDIR}/*
rmdir ${WORKDIR}