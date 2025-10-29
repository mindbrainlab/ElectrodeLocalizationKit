from enum import Enum


class DetectionMethod(Enum):
    """
    Possible cap electrode/marker detection method implementations.
    """

    TRADITIONAL = "TRADITIONAL"
    FRST = "FRST"

    MARKER = "MARKER"
    ELECTRODE_BASIC = "ELECTRODE_BASIC"
    ELECTRODE = "ELECTRODE"
