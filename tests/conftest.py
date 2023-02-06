"""Pytest fixtures."""

from ska_sdp_dataproduct_metadata import config

# Use the config DB memory backend. This will be overridden if the
# FEATURE_CONFIG_DB environment variable is set to 1.
config.FEATURE_CONFIG_DB.set_default(False)
