"""Connect to SDP configuration database."""

import logging
import os

import ska_sdp_config

FEATURE_CONFIG_DB = os.environ.get("FEATURE_CONFIG_DB", True)

LOG = logging.getLogger("ska_sdp_dataproduct_metadata")


def new_config_client():
    """Return an SDP configuration client (factory function)."""
    backend = "etcd3" if FEATURE_CONFIG_DB else "memory"
    LOG.info("Using config DB %s backend", backend)
    config_client = ska_sdp_config.Config(backend=backend)
    return config_client
