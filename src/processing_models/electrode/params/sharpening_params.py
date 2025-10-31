from dataclasses import dataclass


@dataclass
class SharpeningParamsBase:
    """
    Base parameters for sharpening methods.
    """

    sigma: float = 1.5
    strength: float = 2.5
    threshold: float = 10.0


@dataclass
class AdaptiveSharpeningParams(SharpeningParamsBase):
    """
    Parameters for adaptive sharpening.
    """

    enabled: bool = False


@dataclass
class SelectiveSharpeningParams(SharpeningParamsBase):
    """
    Parameters for selective sharpening.
    """

    enabled: bool = False


@dataclass
class UnsharpMaskingParams(SharpeningParamsBase):
    """
    Parameters for unsharp masking.
    """

    enabled: bool = True
