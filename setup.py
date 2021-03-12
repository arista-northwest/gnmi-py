# -*- coding: utf-8 -*-
# Copyright (c) 2018 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import io
import os
import re
from setuptools import setup, find_packages

# here = path.abspath(path.dirname(__file__))
version = None
long_description = None

with io.open('gnmi/__init__.py', 'rt', encoding='utf8') as f:
    version = re.search(r'__version__ = \"(.*?)\"', f.read()).group(1)

with open(os.path.join('README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='gnmi-py',
    version=version,
    description="Python gNMI Client",
    long_description=long_description,
    long_description_content_type='text/markdown',
    py_modules=['gnmi'],
    install_requires=[
        "grpcio>=1.28.1",
        "grpcio-tools>=1.28.1",
        "protobuf>=3.11.3",
        "toml>=0.10.0",
        "typing-extensions>=3.7.4.2"
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
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
    url = "https://github.com/arista-northwest/gnmi-py",
    license = "MIT Licesnse",
    entry_points = {
        'console_scripts': [
            'gnmipy = gnmi.entry:main',
            'gimpy = gnmi.entry:main'
        ]
    }
)