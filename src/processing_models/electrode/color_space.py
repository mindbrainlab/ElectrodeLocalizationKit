import cv2
import numpy as np

from enum import Enum
from typing import List, Dict


class ColorSpace(Enum):
    """
    Possible color spaces for electrode detection.
    """

    RGB = "RGB"
    HSV = "HSV"
    LAB = "LAB"
    YUV = "YUV"
    GRAY = "GRAY"

    @staticmethod
    def transform_color_spaces(
        image: np.ndarray,
        color_spaces: List["ColorSpace"],
    ) -> Dict["ColorSpace", np.ndarray]:
        """
        Transform an image to multiple color spaces with robust error handling.
        """
        # Color space conversion mapping
        conversion_map = {
            ColorSpace.HSV: (cv2.COLOR_RGB2HSV, 3),
            ColorSpace.LAB: (cv2.COLOR_RGB2LAB, 3),
            ColorSpace.YUV: (cv2.COLOR_RGB2YUV, 3),
            ColorSpace.GRAY: (cv2.COLOR_RGB2GRAY, 1),
        }

        transformed: Dict[ColorSpace, np.ndarray] = {}
        for color_space in color_spaces:
            if color_space == ColorSpace.RGB:
                # Keep the original image
                transformed[color_space] = image
            else:
                try:
                    conv_code, num_channels = conversion_map[color_space]
                    converted = cv2.cvtColor(image, conv_code)

                    # Check channels if needed
                    if num_channels == 1 and converted.ndim != 2:
                        raise ValueError(f"Conversion to {color_space} failed to produce grayscale")
                    if num_channels == 3 and (converted.ndim != 3 or converted.shape[2] != 3):
                        raise ValueError(
                            f"Conversion to {color_space} failed to produce 3 channels"
                        )

                    transformed[color_space] = converted

                except KeyError:
                    raise ValueError(f"Unsupported color space: {color_space}")

        return transformed
