from typing import List, Tuple
from dataclasses import dataclass, field

from ..color_space import ColorSpace
from .illumination_correction_params import CLAHEParams
from .noise_reduction_params import BilateralFilterParams, GuidedFilterParams, NLMParams
from .sharpening_params import (
    AdaptiveSharpeningParams,
    SelectiveSharpeningParams,
    UnsharpMaskingParams,
)


@dataclass
class ProcessingParams:
    """
    Parameters for image preprocessing used in view loader.
    """

    # General preprocessing
    target_size: Tuple[int, int] = (1024, 1024)
    gray_world: bool = True
    normalize: bool = False

    # Noise reduction
    bilateral: BilateralFilterParams = field(default_factory=BilateralFilterParams)
    guided: GuidedFilterParams = field(default_factory=GuidedFilterParams)
    nlm: NLMParams = field(default_factory=NLMParams)

    # Illumination correction
    clahe: CLAHEParams = field(default_factory=CLAHEParams)

    # Sharpening
    adaptive: AdaptiveSharpeningParams = field(default_factory=AdaptiveSharpeningParams)
    selective: SelectiveSharpeningParams = field(default_factory=SelectiveSharpeningParams)
    unsharp: UnsharpMaskingParams = field(default_factory=UnsharpMaskingParams)

    # Color space processing
    target_color_spaces: List[ColorSpace] = None

    # Edge enhancement for DoG + Hough
    edge_enhancement: bool = True
    unsharp_mask_strength: float = 1.5

    # Superpixel preprocessing
    superpixel_preprocess: bool = True
    median_filter_size: int = 5

    def __post_init__(self):
        if self.target_color_spaces is None:
            self.target_color_spaces = [ColorSpace.RGB, ColorSpace.HSV, ColorSpace.LAB]
