import cv2
import numpy as np

from typing import Tuple, Literal


class ColorEnhancementUtil:

    @staticmethod
    def enhance_green_channel(
        image: np.ndarray,
        boost_factor: float,
        max_value: float,
        preserve_luminance: bool,
    ) -> np.ndarray:
        """
        Enhance the green channel with controlled boosting.
        """
        # Convert to float for processing
        result = image.astype(np.float32)

        # Preserve luminance option
        if preserve_luminance:
            # Calculate original luminance
            original_luminance = np.mean(result, axis=2)

            # Boost green channel
            result[:, :, 1] = np.minimum(result[:, :, 1] * boost_factor, max_value)

            # Recalculate luminance and normalize
            new_luminance = np.mean(result, axis=2)
            result *= (original_luminance / new_luminance)[:, :, np.newaxis]

        else:
            # Simple green channel boost
            result[:, :, 1] = np.minimum(result[:, :, 1] * boost_factor, max_value)

        return result.astype(np.uint8)

    @staticmethod
    def enhance_green_difference(
        image: np.ndarray,
        excess_boost: float,
        normalization_method: Literal["minmax", "zscore"],
    ) -> np.ndarray:
        """
        Enhance green by emphasizing its difference from other channels.
        """
        # Convert to float for processing
        result = image.astype(np.float32)

        # Calculate green channel excess
        g_excess = result[:, :, 1] - (result[:, :, 0] + result[:, :, 2]) / 2

        # Normalize green excess
        if normalization_method == "minmax":
            # Min-Max normalization
            if g_excess.max() > g_excess.min():
                g_excess_normalized = (
                    (g_excess - g_excess.min()) / (g_excess.max() - g_excess.min()) * 255
                )
            else:
                g_excess_normalized = np.zeros_like(g_excess)
        elif normalization_method == "zscore":
            # Z-score normalization
            mean, std = np.mean(g_excess), np.std(g_excess)
            g_excess_normalized = ((g_excess - mean) / (std + 1e-8)) * 64 + 128
        else:
            raise ValueError(
                f"Unsupported normalization method: {normalization_method}. Use 'minmax' or 'zscore'."
            )

        # Enhance green channel
        enhanced = result.copy()
        enhanced[:, :, 1] = np.minimum(enhanced[:, :, 1] + g_excess_normalized * excess_boost, 255)

        return enhanced.astype(np.uint8)

    @staticmethod
    def enhance_green_in_hsv(
        image: np.ndarray,
        green_hue: float,
        hue_width: float,
        saturation_boost: float,
        value_boost: float,
    ) -> np.ndarray:
        """
        Enhance green regions in HSV color space.
        """
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)

        # Create weight map based on proximity to green hue
        hue_proximity = np.exp(-0.5 * ((hsv[:, :, 0] - green_hue) / hue_width) ** 2)

        # Boost saturation for pixels with hue close to green
        hsv[:, :, 1] = np.minimum(
            hsv[:, :, 1] + hsv[:, :, 1] * hue_proximity * saturation_boost, 255
        )

        # Boost value for pixels with hue close to green
        hsv[:, :, 2] = np.minimum(hsv[:, :, 2] + hsv[:, :, 2] * hue_proximity * value_boost, 255)

        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

    @staticmethod
    def enhance_green_in_lab(
        image: np.ndarray,
        green_lab: Tuple[float, float, float] = (0, -128, 128),
        distance_scale: float = 50.0,
        a_channel_boost: float = 0.5,
    ) -> np.ndarray:
        """
        Enhance green regions in Lab color space.
        """
        # Convert to Lab
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB).astype(np.float32)

        # Calculate distance from reference green point
        lab_distance = np.linalg.norm(lab - np.array(green_lab), axis=2)

        # Create proximity weight map
        lab_proximity = np.exp(-0.5 * (lab_distance / distance_scale) ** 2)

        # Boost a* channel for pixels close to green
        lab[:, :, 1] = np.minimum(
            lab[:, :, 1] + lab[:, :, 1] * lab_proximity * a_channel_boost, 255
        )

        return cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2RGB)
