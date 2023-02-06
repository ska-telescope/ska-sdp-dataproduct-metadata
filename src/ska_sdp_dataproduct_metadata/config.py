"""Connect to SDP configuration database."""

import logging

import ska_sdp_config

from .feature_toggle import FeatureToggle

FEATURE_CONFIG_DB = FeatureToggle("config_db", True)

LOG = logging.getLogger("ska_sdp_dataproduct_metadata")


def new_config_client():
    """Return an SDP configuration client (factory function)."""
    backend = "etcd3" if FEATURE_CONFIG_DB.is_active() else "memory"
    LOG.info("Using config DB %s backend", backend)
    config_client = ska_sdp_config.Config(backend=backend)
    return config_client
