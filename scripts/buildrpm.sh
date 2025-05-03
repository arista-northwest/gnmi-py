#!/bin/bash

yum -y install 

rpmbuild -ba \
    --define '__python python3' \
    --define "_topdir {$HOME}/rpmbuild" \
    --clean {$HOME}/rpmbuild/SPECS/gnmi-py.spec