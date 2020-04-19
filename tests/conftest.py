import os
import sys

import pytest

sys.path.insert(0, os.path.abspath("."))

from gnmi.structures import CertificateStore

GNMI_SECURE = os.environ.get("GNMI_SECURE", "")
GNMI_TARGET: str = os.environ.get("GNMI_TARGET", "")
GNMI_USER = os.environ.get("GNMI_USER", "admin")
GNMI_PASS = os.environ.get("GNMI_PASS", "")
GNMI_ROOT_CERT = os.environ.get("GNMI_ROOT_CERT", "/dev/null")
GNMI_PRIVAE_KEY = os.environ.get("GNMI_PRIVAE_KEY", "/dev/null")
GNMI_CERT_CHAIN = os.environ.get("GNMI_CERT_CHAIN", "/dev/null")
GNMI_AUTH = (GNMI_USER, GNMI_PASS)

@pytest.fixture(scope="session")
def certificates():
    # hostname, _ = GNMI_TARGET.split(":")
    # realname = hostname.split(".")[0] + ".lab.lan"
    with open(GNMI_ROOT_CERT, "r") as fh:
        root_cert = fh.read().encode()
    with open(GNMI_CERT_CHAIN) as fh:
        client_cert = fh.read().encode()
    with open(GNMI_PRIVAE_KEY) as fh:
        client_key = fh.read().encode()

    return CertificateStore(
        certificat_chain=client_cert,
        private_key=client_key,
        root_certificates=root_cert,
    )

@pytest.fixture(scope="session")
def is_secure():
    if GNMI_SECURE:
        return True
    else:
        return False