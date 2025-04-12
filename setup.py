from setuptools import find_packages, setup

setup(
    name="gnmi-py",
    packages=find_packages(exclude=["tests"]),
    install_requires={
        "grpcio>=1.71.0",
        "grpcio-tools==1.71.0",
        "protobuf==5.29.4",
    },
    entry_points={
        'console_scripts': [
            'gnmipy = gnmi:entry.man',
        ],
    }
)