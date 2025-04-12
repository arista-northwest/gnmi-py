from setuptools import find_packages, setup

setup(
    name="gnmi-py",
    version="0.3.0"
    author="Jesse Mather",
    author_email="jmather@arista.com",
    packages=find_packages(exclude=["tests"]),
    install_requires=[
        "grpcio>=1.71.0",
        "grpcio-tools==1.71.0",
        "protobuf==5.29.4",
    ],
    entry_points={
        'console_scripts': [
            'gnmipy = gnmi:entry.man',
        ],
    }
)