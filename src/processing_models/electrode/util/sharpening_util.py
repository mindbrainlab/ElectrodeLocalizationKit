import cv2
import numpy as np

from typing import Optional


class SharpeningUtil:

    @staticmethod
    def adaptive_sharpen(
        image: np.ndarray,
        sigma: float,
        strength: float,
        threshold: float,
    ) -> np.ndarray:
        """
        Apply adaptive sharpening based on edge detection.
        """
        # Convert to float for calculations
        img_float = image.astype(np.float32)

        # Detect edges using Laplacian
        if len(image.shape) == 3:  # Color image
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:  # Already grayscale
            gray = image.copy()

        # Calculate edge map
        laplacian = cv2.Laplacian(gray, cv2.CV_32F)
        edge_map = np.abs(laplacian)

        # Create adaptive mask based on edges
        mask = edge_map > threshold
        mask = mask.astype(np.float32)

        # Smooth the mask to create gradual transitions
        mask = cv2.GaussianBlur(mask, (0, 0), sigma * 2)

        # Apply unsharp mask algorithm
        blurred = cv2.GaussianBlur(img_float, (0, 0), sigma)
        sharpened = img_float + strength * (img_float - blurred)

        # Expand the mask to match image dimensions if it's a color image
        if len(image.shape) == 3:
            mask = np.expand_dims(mask, axis=2)
            mask = np.repeat(mask, 3, axis=2)

        # Apply adaptive blending based on mask
        result = img_float * (1 - mask) + sharpened * mask

        # Clip values to valid range and convert back to original type
        return np.clip(result, 0, 255).astype(image.dtype)

    @staticmethod
    def selective_sharpen(
        image: np.ndarray,
        sigma: float,
        strength: float,
        threshold: Optional[float],
    ) -> np.ndarray:
        """
        Apply selective sharpening with emphasis on t the green channel.
        """
        # Default channel strengths if not provided
        channel_strengths = (
            strength * 0.7,  # Red
            strength,  # Green
            strength * 0.7,  # Blue
        )

        # Split channels
        channels = cv2.split(image)

        # Sharpen each channel with different intensities
        sharpened_channels = [
            SharpeningUtil.unsharp_masking(channels[i], sigma, channel_strengths[i], threshold)
            for i in range(3)
        ]

        # Merge channels
        return cv2.merge(sharpened_channels)

    @staticmethod
    def unsharp_masking(
        image: np.ndarray,
        sigma: float,
        strength: float,
        threshold: Optional[float],
    ) -> np.ndarray:
        """
        Apply unsharp masking for edge enhancement.
        """
        # Input validation
        if not isinstance(image, np.ndarray):
            raise TypeError("Input must be a NumPy array.")

        # Ensure float processing
        image_float = image.astype(np.float32)

        # Create blurred version
        blurred = cv2.GaussianBlur(image_float, (0, 0), sigma)

        # Apply unsharp masking
        sharpened = cv2.addWeighted(image_float, 1.0 + strength, blurred, -strength, 0)

        # Optional thresholding
        if threshold is not None:
            # Create edge mask
            if image_float.ndim == 2:
                # Grayscale image
                edges = cv2.Laplacian(image_float, cv2.CV_32F)
                mask = np.abs(edges) > threshold
                sharpened = image_float + (sharpened - image_float) * mask
            else:
                # Color image
                gray = cv2.cvtColor(image_float, cv2.COLOR_RGB2GRAY)
                edges = cv2.Laplacian(gray, cv2.CV_32F)
                mask = np.abs(edges) > threshold
                mask = mask[:, :, np.newaxis]
                sharpened = image_float + (sharpened - image_float) * mask

        # Clip to valid range
        return np.clip(sharpened, 0, 255).astype(np.uint8)
