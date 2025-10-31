import cv2
import numpy as np

from typing import Optional, List, Literal, Tuple

from ..color_space import ColorSpace


class ColorQuantizationUtil:

    @staticmethod
    def kmeans_quantization(
        image: np.ndarray,
        n_colors: int,
        color_space: ColorSpace,
    ) -> np.ndarray:
        """
        Quantize colors using K-means clustering with flexible color space options.
        """
        # Prepare image for clustering
        if color_space == ColorSpace.LAB:
            # Convert to LAB color space for perceptually uniform quantization
            pixels = cv2.cvtColor(image, cv2.COLOR_RGB2LAB).astype(np.float32)
        elif color_space == ColorSpace.RGB:
            # Use RGB color space
            pixels = image.astype(np.float32)
        else:
            raise ValueError(f"K-means not supported for {color_space} color space.")

        # Reshape pixels for K-means (N_pixels x channels)
        h, w = image.shape[:2]
        pixels_reshaped = pixels.reshape(-1, 3)

        # Perform K-means clustering
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, centers = cv2.kmeans(
            pixels_reshaped, n_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
        )

        # Reconstruct image
        labels = labels.flatten()
        quantized = centers[labels].reshape(h, w, 3)

        # Convert back to original color space if LAB was used
        if color_space == ColorSpace.LAB:
            quantized = cv2.cvtColor(quantized.astype(np.uint8), cv2.COLOR_LAB2RGB)
        else:
            quantized = quantized.astype(np.uint8)

        return quantized

    @staticmethod
    def lab_hsv_quantization(
        image: np.ndarray,
        n_colors: int,
        foreground_mask: Optional[np.ndarray],
        verbose: bool = False,
    ) -> np.ndarray:
        """
        Advanced color quantization with emphasis on green regions.
        """
        # Default max recursion depth
        max_recursion = 24

        # Default green detection criteria
        green_criteria = {
            "hue_min": 30,
            "hue_max": 90,
            "saturation_min": 64,
            "value_min": 64,
        }

        def _lab_quantization(
            image: np.ndarray, n_colors: int, foreground_mask: np.ndarray
        ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
            """
            Quantize image in LAB color space.
            """
            # Convert to LAB
            lab_image = cv2.cvtColor(image, cv2.COLOR_RGB2LAB).astype(np.float32)

            # Extract foreground pixels in LAB space
            foreground_lab = lab_image[foreground_mask]

            # Check for valid foreground pixels
            if len(foreground_lab) == 0:
                return None, None

            # K-means clustering
            try:
                criteria = (
                    cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
                    100,
                    0.2,
                )
                _, labels, centers = cv2.kmeans(
                    foreground_lab,
                    n_colors,
                    None,
                    criteria,
                    10,
                    cv2.KMEANS_RANDOM_CENTERS,
                )
                return labels, centers
            except cv2.error:
                return None, None

        def _hsv_quantization(
            image: np.ndarray, n_colors: int, foreground_mask: np.ndarray
        ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
            """
            Quantize image with special handling for green regions.
            """
            # Convert to LAB and HSV
            lab_image = cv2.cvtColor(image, cv2.COLOR_RGB2LAB).astype(np.float32)
            hsv_image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)

            # Green region detection
            green_mask = (
                (hsv_image[:, :, 0] >= green_criteria["hue_min"])
                & (hsv_image[:, :, 0] <= green_criteria["hue_max"])
                & (hsv_image[:, :, 1] >= green_criteria["saturation_min"])
                & (hsv_image[:, :, 2] >= green_criteria["value_min"])
            )

            # Combined mask: foreground AND green
            green_foreground_mask = foreground_mask & green_mask

            # Prepare pixels
            foreground_lab = lab_image[foreground_mask]

            if len(foreground_lab) == 0:
                return None, None

            # If green foreground pixels exist, weight them
            if np.any(green_foreground_mask):
                green_lab_pixels = lab_image[green_foreground_mask]

                if len(green_lab_pixels) > 0:
                    # Combine regular foreground with duplicated green pixels
                    weighted_pixels = np.vstack([foreground_lab] + [green_lab_pixels] * 5)

                    try:
                        criteria = (
                            cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
                            100,
                            0.2,
                        )
                        _, labels_weighted, centers_weighted = cv2.kmeans(
                            weighted_pixels,
                            n_colors,
                            None,
                            criteria,
                            10,
                            cv2.KMEANS_RANDOM_CENTERS,
                        )

                        # Recompute cluster assignments
                        distances = np.zeros((len(foreground_lab), n_colors), dtype=np.float32)
                        for i in range(n_colors):
                            distances[:, i] = np.sum(
                                (foreground_lab - centers_weighted[i]) ** 2, axis=1
                            )
                        labels = np.argmin(distances, axis=1)

                        return labels, centers_weighted
                    except cv2.error:
                        return None, None

            return None, None

        def _detect_green_clusters(centers: np.ndarray) -> np.ndarray:
            """
            Identify green clusters based on HSV color space.
            """
            # Convert centers to HSV
            centers_hsv = np.zeros((centers.shape[0], 3), dtype=np.uint8)
            for i, center in enumerate(centers):
                # Create a temporary 1x1 image with the LAB color
                temp_lab = np.zeros((1, 1, 3), dtype=np.uint8)
                temp_lab[0, 0] = center.astype(np.uint8)

                # Convert to HSV
                temp_rgb = cv2.cvtColor(temp_lab, cv2.COLOR_LAB2RGB)
                temp_hsv = cv2.cvtColor(temp_rgb, cv2.COLOR_RGB2HSV)
                centers_hsv[i] = temp_hsv[0, 0]

            # Calculate "greenness" metric for each cluster center
            green_clusters = centers_hsv[
                (centers_hsv[:, 0] >= green_criteria["hue_min"])
                & (centers_hsv[:, 0] <= green_criteria["hue_max"])
                & (centers_hsv[:, 1] >= green_criteria["saturation_min"])
                & (centers_hsv[:, 2] >= green_criteria["value_min"])
            ]

            return green_clusters

        # Prepare foreground mask
        if foreground_mask is None:
            foreground_mask = np.ones(image.shape[:2], dtype=bool)

        # Extract foreground indices
        foreground_indices = np.where(foreground_mask)

        # LAB quantization
        verbose and print("Quantizing in LAB color space...")
        labels, centers = _lab_quantization(image, n_colors, foreground_mask)

        # Check green clusters
        if labels is None or centers is None:
            return image

        green_clusters = _detect_green_clusters(centers)

        # If not enough green clusters, try HSV approach
        if len(green_clusters) < 1:
            verbose and print("No green clusters found, trying quantization in HSV color space...")
            labels, centers = _hsv_quantization(image, n_colors, foreground_mask)

            if labels is None or centers is None:
                # If quantization fails, increase colors or return original
                return (
                    ColorQuantizationUtil.lab_hsv_quantization(image, n_colors + 2, foreground_mask)
                    if n_colors < max_recursion
                    else image
                )

            green_clusters = _detect_green_clusters(centers)

            # Still no green clusters
            if len(green_clusters) < 1:
                verbose and print(f"No green clusters found, trying {n_colors + 2} colors...")
                return (
                    ColorQuantizationUtil.lab_hsv_quantization(image, n_colors + 2, foreground_mask)
                    if n_colors < max_recursion
                    else image
                )

        # Create output image
        result = image.copy()

        # Map foreground pixels to quantized colors
        for i, (y, x) in enumerate(zip(foreground_indices[0], foreground_indices[1])):
            center_lab = centers[labels[i]]

            # Convert LAB center to RGB
            temp_lab = np.zeros((1, 1, 3), dtype=np.uint8)
            temp_lab[0, 0] = center_lab.astype(np.uint8)
            temp_rgb = cv2.cvtColor(temp_lab, cv2.COLOR_LAB2RGB)
            result[y, x] = temp_rgb[0, 0]

        return result

    @staticmethod
    def median_cut_quantization(
        image: np.ndarray,
        n_colors: int,
        color_reduction_method: Literal["avg", "representative"],
    ) -> np.ndarray:
        """
        Apply median cut algorithm for color quantization.
        """

        def _median_cut_recursive(pixels: np.ndarray, depth: int, method: str) -> List[np.ndarray]:
            """
            Recursively apply median cut to color space.
            """
            # Base case: reached depth or single pixel
            if depth == 0 or len(pixels) <= 1:
                if method == "avg":
                    return np.mean(pixels, axis=0)
                else:  # representative
                    return pixels[len(pixels) // 2]

            # Find channel with highest range
            ranges = np.ptp(pixels, axis=0)
            channel = np.argmax(ranges)

            # Sort by this channel
            sorted_pixels = pixels[pixels[:, channel].argsort()]

            # Split at median
            mid = len(sorted_pixels) // 2

            # Recursively process both halves
            return [
                _median_cut_recursive(sorted_pixels[:mid], depth - 1, method),
                _median_cut_recursive(sorted_pixels[mid:], depth - 1, method),
            ]

        # Flatten image and prepare for recursion
        pixels = image.reshape(-1, 3).astype(np.float32)

        # Determine recursion depth
        depth = int(np.ceil(np.log2(n_colors)))

        # Flatten palette recursively
        def _flatten_palette(colors):
            palette = []

            def _flatten(item):
                if isinstance(item, np.ndarray):
                    palette.append(item)
                else:
                    for subitem in item:
                        _flatten(subitem)

            _flatten(colors)
            return np.array(palette)

        # Generate palette
        palette = _flatten_palette(_median_cut_recursive(pixels, depth, color_reduction_method))

        # Limit to requested number of colors
        if len(palette) > n_colors:
            # Use K-means to further reduce colors if needed
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
            _, _, centers = cv2.kmeans(
                palette, n_colors, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
            )
            palette = centers

        # Map pixels to closest palette color
        quantized = np.zeros_like(pixels)
        for i, pixel in enumerate(pixels):
            # Find closest color in palette
            distances = np.sum((palette - pixel) ** 2, axis=1)
            closest_color_idx = np.argmin(distances)
            quantized[i] = palette[closest_color_idx]

        return quantized.reshape(image.shape).astype(np.uint8)
