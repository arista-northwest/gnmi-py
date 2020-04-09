# -*- coding: utf-8 -*-
# Copyright (c) 2018 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import io
import os
import re
from setuptools import setup, find_packages

with io.open('gnmi/__init__.py', 'rt', encoding='utf8') as f:
    version = re.search(r'__version__ = \"(.*?)\"', f.read()).group(1)

setup(
    name='gnmi-py',
    version=version,
    py_modules=['gnmi'],
    install_requires=[
        "grpcio==1.28.1",
        "grpcio-tools==1.28.1",
        "protobuf==3.11.3",
        "PyYAML==5.3.1",
        "typing-extensions==3.7.4.2"
    ],
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet'
    ],
    packages = find_packages(),
    #package_data={'': ['settings.yml']},
    url = "https://github.com/arista-northwest1/gnmi-py",
    license = "MIT Licesnse",
    entry_points = {
        'console_scripts': [
            'gnmipy = gnmi.entry:main'
        ]
    }
)