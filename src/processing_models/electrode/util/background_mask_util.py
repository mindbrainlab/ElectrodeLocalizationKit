import cv2
import logging
import numpy as np

from typing import Optional, Tuple


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class BackgroundMaskUtil:
    @staticmethod
    def analyze_white_background(image: np.ndarray) -> int:
        """
        Analyze white background characteristics in an RGB image to suggest an optimal sensitivity.
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

        # Strict white mask (very bright, very low saturation)
        strict_white_mask = cv2.inRange(hsv, np.array([0, 0, 240]), np.array([255, 15, 255]))

        if np.count_nonzero(strict_white_mask) == 0:
            return 40  # fallback if no white region is detected

        # Extract S and V channels where mask is white
        s_channel = hsv[:, :, 1][strict_white_mask > 0]
        v_channel = hsv[:, :, 2][strict_white_mask > 0]

        # Compute statistics more efficiently
        s_mean, s_std = cv2.meanStdDev(s_channel)
        v_mean, v_std = cv2.meanStdDev(v_channel)

        s_max = int(np.max(s_channel))
        v_min = int(np.min(v_channel))

        # Base sensitivity depending on background brightness/variation
        if s_max < 10 and v_min > 245:
            base = 8  # pure white
        elif s_max < 25 and v_min > 220:
            base = 20  # paper white
        elif s_max < 40 and v_min > 180:
            base = 35  # lit but uneven
        else:
            base = 50  # shadowed

        # Adjustment based on variation
        adjustment = min(int(s_std * 2 + v_std * 0.5), 20)
        sensitivity = base + adjustment

        return max(0, min(100, sensitivity))  # clamp

    @staticmethod
    def generate_background_mask(
        image: np.ndarray,
        sensitivity: Optional[int] = None,
        kernel_size: Tuple[int, int] = (25, 25),
    ) -> np.ndarray:
        """
        Generate a binary mask for white or near-white backgrounds.
        """
        if sensitivity is None:
            sensitivity = BackgroundMaskUtil.analyze_white_background(image)
            logging.info(f"Auto-detected sensitivity: {sensitivity}")

        sensitivity = max(0, min(100, sensitivity))

        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

        # Define thresholds for white/near-white detection
        lower_white = np.array([0, 0, 255 - sensitivity])
        upper_white = np.array([255, sensitivity, 255])
        mask = cv2.inRange(hsv, lower_white, upper_white)

        if kernel_size[0] > 0 and kernel_size[1] > 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, kernel_size)

            # First remove small noise
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            # Then close small gaps
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        return mask
