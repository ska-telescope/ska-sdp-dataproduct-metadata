# pylint: disable=too-few-public-methods

"""IVOA ObsCore Attributes"""


class ObsCore:
    """
    SKA-specific possible values for ObsCore attributes
    """

    UNKNOWN = "Unknown"
    SKA = "SKA-Observatory"
    SKA_LOW = "SKA-LOW"
    SKA_MID = "SKA-MID"

    class DataProductType:
        """
        A simple string value describing the primary nature
        of the data product
        """

        MS = "MS"
        UNKNOWN = "Unknown"

    class CalibrationLevel:
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

    class ObservationCollection:
        """
        A string identifying the data collection to which
        the data product belongs
        """

        UNKNOWN = "Unknown"
        SIMULATION = "Simulation"

    class AccessFormat:
        """
        The format (mime-type) of the data product if downloaded as a file
        """

        UNKNOWN = "application/unknown"
        TAR_GZ = "application/x-tar-gzip"
