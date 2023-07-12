"""IVOA ObsCore Attributes"""

from dataclasses import dataclass
from enum import Enum


@dataclass
class ObsCore:
    """
    SKA-specific possible values for ObsCore attributes
    """

    UNKNOWN = "Unknown"
    SKA = "SKA-Observatory"
    SKA_LOW = "SKA-LOW"
    SKA_MID = "SKA-MID"

    class DataProductType(str, Enum):
        """
        A simple string value describing the primary nature
        of the data product
        """

        MS = "MS"
        UNKNOWN = "Unknown"

    class CalibrationLevel(int, Enum):
        """
        The amount of calibration processing that has been
        applied to create the data product
        Refer to the IVOA standard for a full description
        of the categories
        """

        LEVEL_0 = 0
        LEVEL_1 = 1
        LEVEL_2 = 2
        LEVEL_3 = 3
        LEVEL_4 = 4

    class ObservationCollection(str, Enum):
        """
        A string identifying the data collection to which
        the data product belongs
        """

        UNKNOWN = "Unknown"
        SIMULATION = "Simulation"

    class AccessFormat(str, Enum):
        """
        The format (mime-type) of the data product if downloaded as a file
        """

        UNKNOWN = "application/unknown"
        TAR_GZ = "application/x-tar-gzip"
