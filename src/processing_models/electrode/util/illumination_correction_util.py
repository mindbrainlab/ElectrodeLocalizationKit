import cv2
import numpy as np

from typing import Literal, Tuple

from ..color_space import ColorSpace


class IlluminationCorrectionUtil:

    @staticmethod
    def clahe_equalization(
        image: np.ndarray,
        clip_limit: float,
        tile_grid_size: Tuple[int, int],
        color_space: Literal[ColorSpace.LAB, ColorSpace.YUV],
    ) -> np.ndarray:
        """
        Apply Contrast Limited Adaptive Histogram Equalization (CLAHE)
        to normalize image lighting.

        Reference: https://ieeexplore.ieee.org/document/109340
        Alternatives:
        - https://arxiv.org/pdf/2004.07945 (Adaptive Local Contrast Normalization)
        - https://www.ipol.im/pub/art/2014/107/article_lr.pdf (Multi-Scale Retinex)
        """
        # CLAHE object
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)

        # Processing based on color space
        if color_space == ColorSpace.LAB:
            # Convert to LAB
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)

            # Split channels
            l, a, b = cv2.split(lab)

            # Apply CLAHE to L channel
            l_clahe = clahe.apply(l)

            # Merge and convert back to RGB
            lab_clahe = cv2.merge((l_clahe, a, b))
            return cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2RGB)

        elif color_space == ColorSpace.YUV:
            # Convert to YUV
            yuv = cv2.cvtColor(image, cv2.COLOR_RGB2YUV)

            # Split channels
            y, u, v = cv2.split(yuv)

            # Apply CLAHE to luminance channel
            y_eq = clahe.apply(y)

            # Merge and convert back to RGB
            yuv_eq = cv2.merge((y_eq, u, v))
            return cv2.cvtColor(yuv_eq, cv2.COLOR_YUV2RGB)

        else:
            raise ValueError(f"CLAHE not supported for {color_space} color space.")
