import cv2

from dataclasses import dataclass

from ..color_space import ColorSpace


@dataclass
class BilateralFilterParams:
    """
    Parameters for bilateral filtering.
    """

    enabled: bool = True
    diameter: int = 9
    sigma_color: float = 75.0
    sigma_space: float = 75.0
    border_type: int = cv2.BORDER_REFLECT_101


@dataclass
class GuidedFilterParams:
    """
    Parameters for guided filtering.
    """

    enabled: bool = False
    radius: int = 3
    epsilon: float = 1e-3
    color_space: ColorSpace = ColorSpace.LAB


@dataclass
class NLMParams:
    """
    Parameters for non-local means denoising.
    """

    enabled: bool = False
    filtering_strength: float = 5.0
    template_window_size: int = 7
    search_window_size: int = 21
    color_space: ColorSpace = ColorSpace.LAB
