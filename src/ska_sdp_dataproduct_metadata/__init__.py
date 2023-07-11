"""SDP Data Product Metadata."""

from .config import new_config_client
from .metadata import MetaData
from .obscore import ObsCore

__all__ = ["MetaData", "ObsCore", "new_config_client"]
