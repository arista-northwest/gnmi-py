from setuptools import find_packages, setup

setup(
    name="gnmi-py",
    version="0.4.0",
    author="Jesse Mather",
    author_email="jmather@arista.com",
    license="MIT",
    description="gNMI client",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "grpcio==1.62.3",
        "grpcio-tools==1.62.3",
        "protobuf==4.25.1",
    ],
    entry_points={
        'console_scripts': [
            'gnmipy = gnmi.entry:main',
        ],
    }
)
