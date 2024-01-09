"""IVOA ObsCore Attributes"""

from dataclasses import dataclass
from enum import Enum


@dataclass
class ObsCore:
    """
    SKA-specific possible values for ObsCore attributes
    """

    SKA = "SKA-Observatory"
    SKA_LOW = "SKA-LOW"
    SKA_MID = "SKA-MID"
    UNKNOWN = "Unknown"

    class DataProductType(str, Enum):
        """
        A simple string value describing the primary nature
        of the data product
        """

        MS = "MS"
        POINTING = "POINTING-OFFSETS"
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

        SIMULATION = "Simulation"
        UNKNOWN = "Unknown"

    class UCD(str, Enum):
        """
        A list of Unified Content Descriptors (Preite Martinez, et al. 2007)
        describing the nature of the observable within the data product
        https://www.ivoa.net/documents/latest/UCDlist.html
        """

        COUNT = "phot.count"
        FLUX_DENSITY = "phot.flux.density"
        FOURIER = "stat.fourier"

    class AccessFormat(str, Enum):
        """
        The format (mime-type) of the data product if downloaded as a file
        """

        BINARY = "application/octet-stream"
        FITS = "image/fits"
        HDF5 = "application/x-hdf5"
        JPEG = "image/jpeg"
        PNG = "image/png"
        TAR_GZ = "application/x-tar-gzip"
        UNKNOWN = "application/unknown"
