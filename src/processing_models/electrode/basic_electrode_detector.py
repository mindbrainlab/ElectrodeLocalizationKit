import cv2
import logging
import numpy as np

from typing import List, Optional, Tuple

from .frst import FRST
from .view_type import ViewType
from .color_space import ColorSpace
from .detection_method import DetectionMethod
from .util import ColorEnhancementUtil, NoiseReductionUtil


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class BasicElectrodeDetector:

    def __init__(
        self,
        min_area: Optional[int] = None,
        min_distance: Optional[int] = None,
        min_radius: Optional[int] = None,
        max_radius: Optional[int] = None,
    ) -> None:
        """
        Initialize basic electrode detector.
        """
        self.min_area = min_area
        self.min_distance = min_distance
        self.min_radius = min_radius
        self.max_radius = max_radius

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Reduce noise, and normalize image to grayscale.
        """
        # Reduce the green color markers
        image = ColorEnhancementUtil.enhance_green_in_hsv(image, 60.0, 25.0, -2.5, 1.5)

        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)
        h, s, v = cv2.split(hsv)

        # Darken very dark pixels further to boost contrast
        dark_mask = v < 128
        v[dark_mask] = np.clip(v[dark_mask] * 0.5, 0, 255)
        hsv_boosted = cv2.merge([h, s, v])
        rgb_boosted = cv2.cvtColor(hsv_boosted.astype(np.uint8), cv2.COLOR_HSV2RGB)

        # Denoise and convert to grayscale
        denoised = NoiseReductionUtil.nlm_denoising(rgb_boosted, 25.0, ColorSpace.LAB)
        grayscale = cv2.cvtColor(denoised, cv2.COLOR_RGB2GRAY)

        # Normalize intensities to 0–255
        normalized = cv2.normalize(grayscale, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        return normalized

    def _apply_morphological_operations(self, binary_mask: np.ndarray) -> np.ndarray:
        """
        Clean up binary mask with opening and closing operations.
        """
        kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10))
        kernel_large = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))

        # Remove small noise with opening
        opened = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel_small)

        # Fill small holes with closing
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel_large)

        # Make structures a bit smaller again
        reopened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel_small)

        # Refine shapes with erosion-dilation
        eroded = cv2.erode(reopened, kernel_small, iterations=1)
        refined = cv2.dilate(eroded, kernel_large, iterations=1)

        return refined

    def _filter_contours(
        self,
        morph_mask: np.ndarray,
        view_type: ViewType,
        use_frst: bool = False,
    ) -> np.ndarray:
        """
        Keep only contours that look like circular electrodes.
        """
        contours, _ = cv2.findContours(morph_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        filtered = np.zeros_like(morph_mask)

        for contour in contours:
            area = cv2.contourArea(contour)
            min_area = self.min_area or view_type.electrode_cfg.min_area or 500
            if area < min_area:
                continue

            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue

            circularity = 4 * np.pi * area / (perimeter * perimeter)
            min_circularity = 0.5 if use_frst else 0.75
            if circularity <= min_circularity:
                continue

            cv2.drawContours(filtered, [contour], -1, 255, -1)

        return filtered

    def get_electrode_mask(
        self,
        image: np.ndarray,
        foreground_mask: np.ndarray,
        view_type: ViewType,
        methods: List[DetectionMethod],
    ) -> np.ndarray:
        """
        Detect electrode regions using one or more detection methods and combine their results into a single mask.
        """
        if not methods:
            # Return full mask if no methods are provided
            return np.ones(image.shape[:2], dtype=np.uint8) * 255

        # Start with an empty mask
        electrode_mask = np.zeros(image.shape[:2], dtype=np.uint8)

        if DetectionMethod.TRADITIONAL in methods:
            grayscale = self._preprocess_image(image)
            _, binary = cv2.threshold(grayscale, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            binary = cv2.bitwise_and(binary, binary, mask=foreground_mask)
            morph_mask = self._apply_morphological_operations(binary)
            traditional_mask = self._filter_contours(morph_mask, view_type, use_frst=False)
            electrode_mask = cv2.bitwise_or(electrode_mask, traditional_mask)

        if DetectionMethod.FRST in methods:
            grayscale = self._preprocess_image(image)
            tophat_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            tophat = cv2.morphologyEx(grayscale, cv2.MORPH_TOPHAT, tophat_kernel)
            frst_input = cv2.subtract(grayscale, tophat)

            radii_range = list(range(15, 50, 5))
            frst = FRST()
            frst_response = frst.run(frst_input, radii_range, alpha=1.0, beta=0.1)

            eroded_mask = cv2.erode(
                foreground_mask,
                cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10)),
                iterations=1,
            )
            frst_response = cv2.bitwise_and(
                frst_response, frst_response, mask=eroded_mask.astype(np.uint8)
            )

            frst_normalized = cv2.normalize(frst_response, None, 0, 255, cv2.NORM_MINMAX).astype(
                np.uint8
            )
            _, frst_binary = cv2.threshold(
                frst_normalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            frst_binary = cv2.bitwise_and(frst_binary, frst_binary, mask=foreground_mask)

            morph_mask = self._apply_morphological_operations(frst_binary)
            frst_mask = self._filter_contours(morph_mask, view_type, use_frst=True)
            electrode_mask = cv2.bitwise_or(electrode_mask, frst_mask)

        return electrode_mask

    def _apply_dog_and_hough(
        self,
        original_image: np.ndarray,
        grayscale: np.ndarray,
        filtered_mask: np.ndarray,
        view_type: ViewType,
        use_frst: bool = False,
    ) -> Optional[np.ndarray]:
        """
        Detect circles using Difference of Gaussians + Hough Circle Transform.
        """
        # Apply DoG filtering
        masked = cv2.bitwise_and(grayscale, grayscale, mask=filtered_mask)
        blur_small = cv2.GaussianBlur(masked.astype(np.float32), (0, 0), 2.5)
        blur_large = cv2.GaussianBlur(masked.astype(np.float32), (0, 0), 5.0)
        dog = blur_small - blur_large

        dog_normalized = cv2.normalize(dog, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        dog_filtered = cv2.medianBlur(dog_normalized, 5)

        # Hough Circle parameters
        param2 = 25 if use_frst else 30
        min_dist = self.min_distance or view_type.electrode_cfg.min_distance or 50
        min_r = self.min_radius or view_type.electrode_cfg.min_radius or 10
        max_r = self.max_radius or view_type.electrode_cfg.max_radius or 25

        circles = cv2.HoughCircles(
            dog_filtered,
            cv2.HOUGH_GRADIENT,
            dp=1.0,
            minDist=min_dist,
            param1=50,
            param2=param2,
            minRadius=min_r,
            maxRadius=max_r,
        )

        # Validate detected circles
        if circles is not None:
            circles = np.uint16(np.around(circles))
            valid_circles = []

            gray_original = cv2.cvtColor(original_image, cv2.COLOR_RGB2GRAY)

            for x, y, r in circles[0, :]:
                if y >= filtered_mask.shape[0] or x >= filtered_mask.shape[1]:
                    continue

                if filtered_mask[y, x] > 0 and gray_original[y, x] < 200:
                    valid_circles.append((x, y, r))

            circles = np.array([valid_circles], dtype=np.uint16) if valid_circles else None

        return circles

    def detect_traditional(
        self,
        image: np.ndarray,
        foreground_mask: np.ndarray,
        view_type: ViewType,
    ) -> Optional[np.ndarray]:
        """
        Detect electrodes using thresholding + morphology + Hough transform.
        """
        grayscale = self._preprocess_image(image)

        _, binary = cv2.threshold(grayscale, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        binary = cv2.bitwise_and(binary, binary, mask=foreground_mask)

        morph_mask = self._apply_morphological_operations(binary)
        electrode_mask = self._filter_contours(morph_mask, view_type, use_frst=False)

        return self._apply_dog_and_hough(
            image, grayscale, electrode_mask, view_type, use_frst=False
        )

    def detect_frst(
        self,
        image: np.ndarray,
        foreground_mask: np.ndarray,
        view_type: ViewType,
    ) -> Optional[np.ndarray]:
        """
        Detect electrodes using FRST (Fast Radial Symmetry Transform).
        """
        grayscale = self._preprocess_image(image)

        # Enhance circular structures
        tophat_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        tophat = cv2.morphologyEx(grayscale, cv2.MORPH_TOPHAT, tophat_kernel)
        frst_input = cv2.subtract(grayscale, tophat)

        radii_range = list(range(15, 50, 5))
        frst = FRST()
        frst_response = frst.run(frst_input, radii_range, alpha=1.0, beta=0.1)

        # Apply foreground mask
        eroded_mask = cv2.erode(
            foreground_mask,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (10, 10)),
            iterations=1,
        )
        frst_response = cv2.bitwise_and(
            frst_response, frst_response, mask=eroded_mask.astype(np.uint8)
        )

        frst_normalized = cv2.normalize(frst_response, None, 0, 255, cv2.NORM_MINMAX).astype(
            np.uint8
        )
        _, frst_binary = cv2.threshold(frst_normalized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        frst_binary = cv2.bitwise_and(frst_binary, frst_binary, mask=foreground_mask)

        morph_mask = self._apply_morphological_operations(frst_binary)
        electrode_mask = self._filter_contours(morph_mask, view_type, use_frst=True)

        return self._apply_dog_and_hough(image, grayscale, electrode_mask, view_type, use_frst=True)

    def _combine_results(
        self,
        view_type: ViewType,
        circles_traditional: Optional[np.ndarray],
        circles_frst: Optional[np.ndarray],
    ) -> Optional[np.ndarray]:
        """
        Merge circles from both methods, removing overlaps.
        """
        combined = []

        if circles_traditional is not None:
            combined.extend(
                (float(x), float(y), float(r), "traditional") for x, y, r in circles_traditional[0]
            )
        if circles_frst is not None:
            combined.extend((float(x), float(y), float(r), "frst") for x, y, r in circles_frst[0])

        if not combined:
            return None

        if len({m for _, _, _, m in combined}) == 1:
            return np.array([[(x, y, r) for x, y, r, _ in combined]], dtype=np.uint16)

        # Remove overlaps, keep larger circles
        unique = []
        for x1, y1, r1, method1 in sorted(combined, key=lambda c: c[2], reverse=True):
            overlap = False
            for i, (x2, y2, r2, method2) in enumerate(unique):
                dist = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
                min_dist = self.min_distance or view_type.electrode_cfg.min_distance or 0
                if dist < (r1 + r2) or dist < min_dist:
                    if r1 > r2:
                        unique[i] = (x1, y1, r1, method1)
                    overlap = True
                    break
            if not overlap:
                unique.append((x1, y1, r1, method1))

        return np.array([[(x, y, r) for x, y, r, _ in unique]], dtype=np.uint16) if unique else None

    @staticmethod
    def draw_circles(image: np.ndarray, circles: np.ndarray) -> np.ndarray:
        """
        Draw detected circles and their centers.
        """
        output = image.copy()
        if circles is not None:
            for x, y, r in np.uint16(np.around(circles))[0, :]:
                cv2.circle(output, (x, y), r, (0, 255, 0), 3)
                cv2.circle(output, (x, y), 2, (255, 0, 0), 5)
        return output

    def detect(
        self,
        image: np.ndarray,
        foreground_mask: np.ndarray,
        view_type: ViewType,
        methods: List[DetectionMethod],
    ) -> Tuple[Optional[np.ndarray], np.ndarray]:
        """
        Detect electrodes using selected methods and combine results.
        """
        circles_traditional, circles_frst = None, None

        if DetectionMethod.TRADITIONAL in methods:
            logging.info("Running traditional electrode detection...")
            circles_traditional = self.detect_traditional(image, foreground_mask, view_type)

        if DetectionMethod.FRST in methods:
            logging.info("Running FRST electrode detection...")
            circles_frst = self.detect_frst(image, foreground_mask, view_type)

        circles = self._combine_results(view_type, circles_traditional, circles_frst)
        output_image = self.draw_circles(image, circles)

        return circles, output_image
