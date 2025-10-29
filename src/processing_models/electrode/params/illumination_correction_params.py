from typing import Tuple
from dataclasses import dataclass

from ..color_space import ColorSpace


@dataclass
class CLAHEParams:
    """
    Parameters for contrast limited adaptive histogram equalization.
    """

    enabled: bool = True
    clip_limit: float = 2.5
    tile_grid_size: Tuple[int, int] = (8, 8)
    color_space: ColorSpace = ColorSpace.LAB
