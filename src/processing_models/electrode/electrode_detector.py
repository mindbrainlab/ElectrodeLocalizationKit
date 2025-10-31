import cv2
import logging
import numpy as np

from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from typing import Dict, List, Optional, Tuple, Union
from skimage.segmentation import slic, mark_boundaries

from .frst import FRST
from .view_type import ViewType
from .color_space import ColorSpace
from .detection_method import DetectionMethod
from .basic_electrode_detector import BasicElectrodeDetector
from .util import ColorEnhancementUtil, ColorQuantizationUtil, NoiseReductionUtil


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class ElectrodeDetector:

    def __init__(
        self,
        min_distance: Optional[int] = None,
        n_segments: Optional[int] = None,
    ):
        """
        Initialize the superpixel segmentation electrode detector.
        """
        self.min_distance = min_distance
        self.n_segments = n_segments

    def _preprocess_image(self, image: np.ndarray, foreground_mask: np.ndarray) -> np.ndarray:
        """
        Preprocess the input image for electrode detection.
        """
        logging.info("Preprocessign image for electrode detection...")

        # Reduce green color markers
        image = ColorEnhancementUtil.enhance_green_in_hsv(image, 60.0, 25.0, -2.5, 1.5)

        # Boost contrast in dark regions
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV).astype(np.float32)
        h, s, v = cv2.split(hsv)
        dark_mask = v < 128
        v[dark_mask] = np.clip(v[dark_mask] * 0.5, 0, 255)
        hsv_boosted = cv2.merge([h, s, v])
        rgb_boosted = cv2.cvtColor(hsv_boosted.astype(np.uint8), cv2.COLOR_HSV2RGB)

        # Color quantization in LAB + HSV spaces
        processed = ColorQuantizationUtil.lab_hsv_quantization(image, 8, foreground_mask)

        # Non-local means denoising in LAB color space
        denoised = NoiseReductionUtil.nlm_denoising(processed, 50.0, ColorSpace.LAB)

        # Normalize intensities
        normalized = cv2.normalize(denoised, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        return normalized

    def _apply_slic_segmentation(
        self, image: np.ndarray, foreground_mask: np.ndarray, view_type: ViewType
    ) -> np.ndarray:
        """
        Apply SLIC superpixel segmentation to the image.
        """
        n_segments = self.n_segments or view_type.electrode_cfg.n_segments or 750
        logging.info(f"Applying SLIC segmentation with {n_segments} segments...")

        # Apply SLIC superpixel segmentation
        segments = slic(
            image=image,
            n_segments=n_segments,
            compactness=25.0,  # Balance between color similarity and spatial proximity
            max_num_iter=25,  # Maximum number of k-means iterations
            sigma=1.0,  # Gaussian smoothing kernel width
            convert2lab=True,  # Convert to LAB color space
            enforce_connectivity=True,  # Ensure connected superpixels
            start_label=1,  # Start labeling from 1 (0 reserved for background)
            mask=foreground_mask > 0,  # Only segment foreground regions
            channel_axis=-1,  # Color channels are in the last dimension
        )

        unique_segments = len(np.unique(segments))
        logging.info(f"Generated {unique_segments} superpixels")

        return segments

    def _find_background_neighbors(self, segments: np.ndarray) -> np.ndarray:
        """
        Find superpixels that are neighbors of the background (segment 0).
        """
        background_positions = np.argwhere(segments == 0)
        neighbors_of_background = set()

        height, width = segments.shape

        for row, col in background_positions:
            # Check 4-connected neighbors
            neighbor_coords = [
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ]

            for r, c in neighbor_coords:
                if 0 <= r < height and 0 <= c < width:
                    neighbor_id = segments[r, c]
                    if neighbor_id != 0:  # Not background
                        neighbors_of_background.add(neighbor_id)

        return neighbors_of_background

    def _extract_geometric_features(self, segment_mask: np.ndarray) -> Dict[str, Union[float, int]]:
        """
        Extract geometric features from a segment mask.
        """
        # Find contours
        contours, _ = cv2.findContours(
            segment_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if len(contours) == 0:
            # Default values for empty contours
            return {
                "area": np.sum(segment_mask),
                "perimeter": 0,
                "circularity": 0,
                "aspect_ratio": 0,
                "eccentricity": 0,
                "solidity": 0,
                "centroid_x": 0,
                "centroid_y": 0,
            }

        # Use the largest contour
        largest_contour = max(contours, key=cv2.contourArea)

        # Basic geometric properties
        area = cv2.contourArea(largest_contour)
        perimeter = cv2.arcLength(largest_contour, closed=True)

        # Circularity (4π*area / perimeter²)
        circularity = 4 * np.pi * area / (perimeter**2) if perimeter > 0 else 0

        # Bounding rectangle and aspect ratio
        x, y, w, h = cv2.boundingRect(largest_contour)
        aspect_ratio = w / h if h > 0 else 0
        centroid_x, centroid_y = x + w / 2, y + h / 2

        # Eccentricity from fitted ellipse
        eccentricity = 1.0  # Default value
        if len(largest_contour) >= 5:  # Need at least 5 points for ellipse fitting
            try:
                (center, axes, orientation) = cv2.fitEllipse(largest_contour)
                major_axis = max(axes)
                minor_axis = min(axes)
                if major_axis > 0:
                    eccentricity = np.sqrt(1 - (minor_axis**2 / major_axis**2))
            except cv2.error:
                eccentricity = 1.0

        # Solidity (area / convex hull area)
        hull = cv2.convexHull(largest_contour)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0

        return {
            "area": area,
            "perimeter": perimeter,
            "circularity": circularity,
            "eccentricity": eccentricity,
            "solidity": solidity,
            "aspect_ratio": aspect_ratio,
            "centroid_x": centroid_x,
            "centroid_y": centroid_y,
        }

    def _compute_local_contrast(
        self,
        gray_image: np.ndarray,
        segment_mask: np.ndarray,
        dilate_size: Optional[int] = 15,
    ) -> float:
        """
        Compute local contrast of a superpixel relative to its surroundings.
        """
        # Calculate mean intensity inside the superpixel
        mean_inside = cv2.mean(gray_image, mask=segment_mask)[0]

        # Create dilated mask to define surrounding region
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate_size, dilate_size))
        dilated_mask = cv2.dilate(segment_mask, kernel)

        # Get surrounding ring by subtracting original mask from dilated mask
        surrounding_mask = cv2.subtract(dilated_mask, segment_mask)

        # Calculate mean intensity of surrounding region
        mean_surrounding = cv2.mean(gray_image, mask=surrounding_mask)[0]

        # Return contrast as difference between inside and surrounding intensities
        return mean_inside - mean_surrounding

    def _extract_superpixel_features(
        self, image: np.ndarray, segments: np.ndarray, foreground_mask: np.ndarray
    ) -> np.ndarray:
        """
        Extract features from each superpixel for electrode classification.
        """
        logging.info("Extracting superpixel features...")

        features_list = []
        segment_ids = np.unique(segments)

        # Convert to LAB color space for color features
        lab_image = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab_image)

        # Compute FRST (Fast Radial Symmetry Transform) response
        frst = FRST()
        frst_response = frst.run(
            lab_image[:, :, 0], radii=list(range(1, 25, 2)), alpha=1.0, beta=0.01
        )

        # Find segments neighboring background (segment 0)
        background_neighbors = self._find_background_neighbors(segments)

        # Convert to grayscale for contrast computation
        gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # Process each superpixel
        for segment_id in segment_ids:
            # Skip background and edge segments
            if segment_id == 0 or segment_id in background_neighbors:
                continue

            segment_mask = (segments == segment_id).astype(np.uint8)

            # Filter out small segments or those mostly in background
            segment_size = np.sum(segment_mask)
            foreground_overlap = np.sum(segment_mask & foreground_mask)

            if segment_size < 5 or foreground_overlap < segment_size * 0.5:
                continue

            # Extract LAB color features
            l_mean = np.mean(l_channel[segment_mask > 0])
            l_std = np.std(l_channel[segment_mask > 0])
            a_mean = np.mean(a_channel[segment_mask > 0])
            b_mean = np.mean(b_channel[segment_mask > 0])

            # Extract geometric features from contours
            geometric_features = self._extract_geometric_features(segment_mask)

            # Compute local contrast
            contrast = self._compute_local_contrast(gray_image, segment_mask, dilate_size=15)

            # Compute mean FRST response
            frst_mean = cv2.mean(frst_response, mask=segment_mask)[0]

            # Combine all features
            features = [
                segment_id,  # 0: Segment ID
                l_mean,  # 1: L channel mean
                l_std,  # 2: L channel standard deviation
                a_mean,  # 3: A channel mean
                b_mean,  # 4: B channel mean
                geometric_features["area"],  # 5: Area
                geometric_features["perimeter"],  # 6: Perimeter
                geometric_features["circularity"],  # 7: Circularity
                geometric_features["eccentricity"],  # 8: Eccentricity
                geometric_features["solidity"],  # 9: Solidity
                geometric_features["aspect_ratio"],  # 10: Aspect ratio
                contrast,  # 11: Local contrast
                frst_mean,  # 12: FRST response mean
                geometric_features["centroid_x"],  # 13: Centroid X
                geometric_features["centroid_y"],  # 14: Centroid Y
                None,  # 15: Confidence (computed later)
            ]

            features_list.append(features)

        logging.info(f"Extracted features from {len(features_list)} superpixels")
        return np.array(features_list)

    def _cluster_superpixels(self, features: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Cluster superpixels using Gaussian Mixture Model to identify electrode candidates.
        """
        logging.info("Clustering superpixels with GMM...")

        # Extract relevant features for clustering (contrast and FRST response)
        feature_indices = [11, 12]  # contrast, frst_mean
        clustering_features = features[:, feature_indices]

        # Apply feature weighting
        feature_weights = np.array([2.0, 1.0])  # Higher weight for contrast
        weighted_features = clustering_features * feature_weights

        # Standardize features
        scaler = StandardScaler()
        normalized_features = scaler.fit_transform(weighted_features)

        # Fit Gaussian Mixture Model
        gmm = GaussianMixture(
            n_components=2,  # Two clusters: electrodes vs non-electrodes
            covariance_type="full",  # Full covariance matrices
            max_iter=250,  # Maximum iterations for convergence
            random_state=42,  # For reproducibility
        )

        cluster_labels = gmm.fit_predict(normalized_features)

        # Identify electrode cluster (assume it's the smaller cluster)
        unique_labels, label_counts = np.unique(cluster_labels, return_counts=True)
        electrode_cluster_id = unique_labels[np.argmin(label_counts)]

        # Extract features of electrode cluster
        electrode_mask = cluster_labels == electrode_cluster_id
        electrode_cluster_features = features[electrode_mask]

        logging.info(
            f"Identified {len(electrode_cluster_features)} electrode candidates from clustering"
        )

        return cluster_labels, electrode_cluster_features

    def _filter_electrode_candidates(
        self,
        image: np.ndarray,
        foreground_mask: np.ndarray,
        view_type: ViewType,
        cluster_features: np.ndarray,
        slic_segments: np.ndarray,
    ) -> np.ndarray:
        """
        Filter electrode candidates based on shape, appearance, and segment location.
        """
        logging.info("Filtering electrode candidates based on shape criteria...")

        valid_candidates = []

        # Generate basic electrode mask
        basic_detector = BasicElectrodeDetector()
        mask = basic_detector.get_electrode_mask(
            image,
            foreground_mask,
            view_type,
            [DetectionMethod.TRADITIONAL, DetectionMethod.FRST],
        )
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, (25, 25))

        for feature_row in cluster_features:
            # Extract relevant features
            segment_id = feature_row[0]
            circularity = feature_row[7]
            eccentricity = feature_row[8]
            solidity = feature_row[9]
            aspect_ratio = feature_row[10]
            contrast = feature_row[11]
            frst_mean = feature_row[12]

            # Shape-based filtering
            shape_criteria_met = (
                circularity >= 0.75
                and eccentricity < 0.75
                and solidity > 0.9
                and aspect_ratio < 1.5
            )

            if not shape_criteria_met:
                continue

            # Check if SLIC segment lies inside the electrode mask
            segment_mask = (slic_segments == segment_id).astype(np.uint8)
            overlap = cv2.bitwise_and(segment_mask, mask)
            overlap_ratio = np.sum(overlap) / max(1, np.sum(segment_mask))  # Avoid div by zero

            if overlap_ratio < 0.5:  # Require at least 50% of the segment inside the mask
                continue

            # Multi-factor confidence score
            shape_score = (circularity + solidity) / 2.0
            confidence = np.abs(contrast) * 0.5 + shape_score * 0.3 + np.abs(frst_mean) * 0.2

            feature_row[15] = confidence
            valid_candidates.append(feature_row)

        return np.array(valid_candidates)

    def _apply_non_maximum_suppression(
        self, candidates: np.ndarray, view_type: ViewType
    ) -> np.ndarray:
        """
        Apply non-maximum suppression to remove closely spaced electrode detections.
        """
        logging.info("Applying non-maximum suppression...")

        # Sort candidates by confidence (highest first)
        sorted_candidates = sorted(candidates, key=lambda x: x[15], reverse=True)

        final_electrodes = []

        for candidate in sorted_candidates:
            candidate_x = float(candidate[13])  # centroid_x
            candidate_y = float(candidate[14])  # centroid_y

            # Check if candidate is too close to already selected electrodes
            too_close = False
            for selected_electrode in final_electrodes:
                selected_x = float(selected_electrode[13])
                selected_y = float(selected_electrode[14])

                distance = np.sqrt(
                    (candidate_x - selected_x) ** 2 + (candidate_y - selected_y) ** 2
                )

                min_dist = self.min_distance or view_type.electrode_cfg.min_distance or 50
                if distance < min_dist:
                    too_close = True
                    break

            # Add candidate if it's not too close to existing selections
            if not too_close:
                final_electrodes.append(candidate)

        logging.info(f"Selected {len(final_electrodes)} final electrodes after NMS")
        return np.array(final_electrodes)

    def _create_output_visualization(
        self, image: np.ndarray, segments: np.ndarray, final_electrodes: np.ndarray
    ) -> np.ndarray:
        """
        Create visualization image showing detected electrodes.
        """
        if len(final_electrodes) == 0:
            return image

        # Extract segment IDs of detected electrodes
        electrode_segment_ids = final_electrodes[:, 0].astype(int)

        # Create mask for electrode segments
        electrode_mask = np.isin(segments, electrode_segment_ids)
        electrode_segments = np.where(electrode_mask, segments, 0)

        # Create visualization with marked boundaries
        output_image = mark_boundaries(
            image,
            electrode_segments,
            color=(1, 0, 0),
            mode="thick",
        )

        return output_image

    def _segments_to_circles(
        self, final_electrodes: np.ndarray
    ) -> List[Tuple[float, float, float]]:
        """
        Convert detected electrodes to circle representations (x, y, r) using equivalent radius.
        """
        if len(final_electrodes) == 0:
            return []

        logging.info(f"Converting {len(final_electrodes)} electrodes to circles...")
        circles = []

        for electrode in final_electrodes:
            centroid_x = float(electrode[13])
            centroid_y = float(electrode[14])
            area = float(electrode[5])

            # Calculate equivalent radius: r = sqrt(area / π)
            radius = np.sqrt(area / np.pi) * 2 if area > 0 else 25

            circles.append((int(centroid_x), int(centroid_y), int(radius)))

        return np.array([circles])

    def detect(
        self, image: np.ndarray, foreground_mask: np.ndarray, view_type: ViewType
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Detect electrodes using SLIC and GMM.
        """
        # Preprocess image
        preprocessed = self._preprocess_image(image, foreground_mask)

        # Apply SLIC segmentation
        segments = self._apply_slic_segmentation(preprocessed, foreground_mask, view_type)

        # Extract features from superpixels
        features = self._extract_superpixel_features(preprocessed, segments, foreground_mask)

        if len(features) == 0:
            logging.warning("No valid superpixels found for feature extraction")
            return np.array([]), image

        # Cluster superpixels to identify electrode candidates
        cluster_labels, electrode_candidates = self._cluster_superpixels(features)

        # Filter candidates based on shape criteria
        filtered_candidates = self._filter_electrode_candidates(
            image, foreground_mask, view_type, electrode_candidates, segments
        )

        if len(filtered_candidates) == 0:
            logging.warning("No electrode candidates passed shape filtering")
            return np.array([]), image

        # Apply non-maximum suppression
        final_electrodes = self._apply_non_maximum_suppression(filtered_candidates, view_type)

        # Create output visualization
        output_segments = self._create_output_visualization(image, segments, final_electrodes)

        # Convert segment to circle
        circles = self._segments_to_circles(final_electrodes)
        output_image = BasicElectrodeDetector.draw_circles(image, circles)

        logging.info(f"Successfully detected {len(final_electrodes)} electrodes")
        return circles, output_image, output_segments
