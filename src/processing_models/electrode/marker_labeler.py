import cv2
import logging
import numpy as np
import matplotlib.pyplot as plt

from dataclasses import dataclass
from typing import Optional, Tuple, Union

from .view_type import ViewType


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


@dataclass
class RegionConfig:
    center: Union[float, Tuple[float, float]]
    tolerance: Optional[float] = None
    angle: Optional[float] = None


class MarkerLabeler:

    BACK_TOP_VERTICAL_LABELS = ["Pz", "POz", "Oz"]
    BACK_TOP_HORIZONTAL_LABELS = ["O1", "Oz", "O2"]
    FRONT_TOP_LABELS = ["Fz"]
    FRONT_RIGHT_LABELS = ["Fp1"]
    FRONT_LEFT_LABELS = ["Fp2"]
    BACK_RIGHT_LABELS = ["TP10"]
    BACK_LEFT_LABELS = ["TP9"]

    def __init__(self):
        """
        Initialize the labeler that handles labeling of EEG markers based on spatial alignment and heuristics.
        """

    def _find_tightest_group(
        self, candidates: np.ndarray, axis: int, group_size: int
    ) -> np.ndarray:
        """
        Find the tightest group of markers along an axis.
        """
        best_group = None
        min_span = float("inf")

        for i in range(len(candidates) - group_size + 1):
            group = candidates[i : i + group_size]
            span = group[-1, axis] - group[0, axis]

            if span < min_span:
                min_span = span
                best_group = group

        return best_group

    def _find_aligned_markers(
        self,
        markers: np.ndarray,
        axis: int,
        center: float,
        tolerance: float,
        min_count: int,
        max_count: int,
    ) -> np.ndarray:
        """
        Find markers aligned along a specific axis.
        """
        # Filter markers within tolerance band
        perp_axis = 1 - axis
        candidates = markers[np.abs(markers[:, perp_axis] - center) < tolerance]

        if len(candidates) == 0:
            return np.array([])

        # Sort along the alignment axis
        candidates = candidates[np.argsort(candidates[:, axis])]

        # If fewer candidates than needed, return none
        if len(candidates) < min_count:
            return np.array([])

        # If more candidates than needed, find tightest group
        if len(candidates) > max_count:
            candidates = self._find_tightest_group(candidates, axis, max_count)

        return candidates

    def _filter_back_top_vertical_markers(
        self,
        markers: np.ndarray,
        width: int,
        tolerance_ratio_x: float = 0.05,
    ) -> Tuple[np.ndarray, list[str], RegionConfig]:
        """
        Select vertically aligned markers around the image center.
        """
        center_x = width / 2
        tolerance_x = width * tolerance_ratio_x

        selected = self._find_aligned_markers(
            markers=markers,
            axis=1,  # Sort by y (vertical)
            center=center_x,
            tolerance=tolerance_x,
            min_count=3,
            max_count=3,
        )

        labels = self.BACK_TOP_VERTICAL_LABELS[: len(selected)]
        config = RegionConfig(center=center_x, tolerance=tolerance_x)

        return selected, labels, config

    def _filter_back_top_horizontal_markers(
        self,
        markers: np.ndarray,
        height: int,
        position_ratio: float = 0.8,
        tolerance_ratio_y: float = 0.1,
    ) -> Tuple[np.ndarray, list[str], RegionConfig]:
        """
        Select horizontally aligned markers at a specific height.
        """
        center_y = height * position_ratio
        tolerance_y = height * tolerance_ratio_y

        selected = self._find_aligned_markers(
            markers=markers,
            axis=0,  # Sort by x (horizontal)
            center=center_y,
            tolerance=tolerance_y,
            min_count=3,
            max_count=3,
        )

        labels = self.BACK_TOP_HORIZONTAL_LABELS[: len(selected)]
        config = RegionConfig(center=center_y, tolerance=tolerance_y)

        return selected, labels, config

    def _find_angled_electrode(
        self,
        candidates: np.ndarray,
        ref_x: float,
        ref_y: float,
        target_angle: float,
        angle_tolerance: float,
        left: bool = False,
        right: bool = False,
    ) -> Optional[np.ndarray]:
        """
        Find electrode at a specific angle from reference point.
        """
        if len(candidates) == 0:
            return None

        best_marker = None
        min_angle_diff = float("inf")

        for marker in candidates:
            dx = float(marker[0]) - float(ref_x)
            dy = float(marker[1]) - float(ref_y)

            # Calculate angle from horizontal
            # For left side: use negative dx to get positive angle
            # For right side: use positive dx
            if left:
                angle = np.arctan2(dy, -dx)
            elif right:
                angle = np.arctan2(dy, dx)
            else:
                return None

            # Check if angle is within tolerance
            angle_diff = abs(angle - target_angle)

            if angle_diff <= angle_tolerance and angle_diff < min_angle_diff:
                min_angle_diff = angle_diff
                best_marker = marker

        return best_marker

    def _filter_front_markers(
        self,
        markers: np.ndarray,
        width: int,
        tolerance_ratio_x: float = 0.05,
        tolerance_angle_degrees: float = 15.0,
    ) -> Tuple[np.ndarray, list[str], RegionConfig, RegionConfig]:
        """
        Select markers that form a triangle near the image center.
        """
        selected = []
        labels = []
        center_x = width / 2
        tolerance_x = width * tolerance_ratio_x

        selected_vertical = self._find_aligned_markers(
            markers=markers,
            axis=1,  # Sort by y (vertical)
            center=center_x,
            tolerance=tolerance_x,
            min_count=1,
            max_count=1,
        )

        if len(selected_vertical) == 0:
            return np.array([]), [], None

        # Find angled markers below the top marker
        top_marker = selected_vertical[0]
        selected.append(top_marker)
        labels.append(self.FRONT_TOP_LABELS[0])
        top_x, top_y = top_marker[0], top_marker[1]
        target_angle_rad = np.radians(90.0 - 30.0)  # 30 degrees from vertical
        tolerance_angle_rad = np.radians(tolerance_angle_degrees)

        # Find left marker
        left_candidates = markers[(markers[:, 0] < center_x) & (markers[:, 1] > top_y)]
        left_marker = self._find_angled_electrode(
            left_candidates,
            top_x,
            top_y,
            target_angle_rad,
            tolerance_angle_rad,
            left=True,
        )
        if left_marker is not None:
            selected.append(left_marker)
            labels.append(self.FRONT_LEFT_LABELS[0])

        # Find right marker
        right_candidates = markers[(markers[:, 0] > center_x) & (markers[:, 1] > top_y)]
        right_marker = self._find_angled_electrode(
            right_candidates,
            top_x,
            top_y,
            target_angle_rad,
            tolerance_angle_rad,
            right=True,
        )
        if right_marker is not None:
            selected.append(right_marker)
            labels.append(self.FRONT_RIGHT_LABELS[0])

        # If left/right markers not found, return closest to the right/left on the same height
        if left_marker is None and len(left_candidates) > 0:
            closest_left = left_candidates[np.argmin(np.abs(left_candidates[:, 0] - top_x))]

            if right_marker is not None:
                # Compare distances from center_x
                dist_left = abs(closest_left[0] - center_x)
                dist_right = abs(right_marker[0] - center_x)
                if np.isclose(dist_left, dist_right, rtol=0.25):  # tolerance 25%
                    selected.append(closest_left)
                    labels.append(self.FRONT_LEFT_LABELS[0])
            else:
                selected.append(closest_left)
                labels.append(self.FRONT_LEFT_LABELS[0])

        if right_marker is None and len(right_candidates) > 0:
            closest_right = right_candidates[np.argmin(np.abs(right_candidates[:, 0] - top_x))]

            if left_marker is not None:
                # Compare distances from center_x
                dist_right = abs(closest_right[0] - center_x)
                dist_left = abs(left_marker[0] - center_x)
                if np.isclose(dist_right, dist_left, rtol=0.25):  # tolerance 25%
                    selected.append(closest_right)
                    labels.append(self.FRONT_RIGHT_LABELS[0])
            else:
                selected.append(closest_right)
                labels.append(self.FRONT_RIGHT_LABELS[0])

        config = RegionConfig(center=(top_x, top_y), tolerance=None, angle=target_angle_rad)

        return np.array(selected), labels, config

    def _filter_back_side_markers(
        self,
        markers: np.ndarray,
        width: int,
        height: int,
        left: bool = False,
        right: bool = False,
    ) -> Tuple[np.ndarray, list[str], RegionConfig]:
        """
        Select vertically aligned markers around the image center.
        """
        selected = []
        labels = []

        center_x = width / 2
        center_y = height / 2

        # Split markers into left and right halves
        left_markers = markers[(markers[:, 0] < center_x) & (markers[:, 1] > center_y)]
        right_markers = markers[(markers[:, 0] >= center_x) & (markers[:, 1] > center_y)]

        # Find the marker with the largest y in each half
        left_marker = left_markers[np.argmax(left_markers[:, 1])] if len(left_markers) > 0 else None
        right_marker = (
            right_markers[np.argmax(right_markers[:, 1])] if len(right_markers) > 0 else None
        )

        if left and left_marker is not None:
            selected.append(left_marker)
            labels.append(self.BACK_LEFT_LABELS[0])
        if right and right_marker is not None:
            selected.append(right_marker)
            labels.append(self.BACK_RIGHT_LABELS[0])

        config = RegionConfig(
            center=(int(center_x), int(center_y)),
            tolerance=None,
            angle=np.radians(45.0),
        )

        return selected, labels, config

    def _assign_labels(
        self,
        markers: np.ndarray,
        selected: np.ndarray,
        labels: list[str],
        labeled_markers: np.ndarray,
    ) -> None:
        """
        Assign labels to selected markers in the labeled array.
        """
        for marker, label in zip(selected, labels):
            # Find index of this marker in original array
            idx = np.where((markers == marker).all(axis=1))[0]

            if len(idx) > 0:
                idx = idx[0]
                # Don't overwrite if label already exists (e.g., "Z" from both filters)
                if labeled_markers[idx, -1] is None or labeled_markers[idx, -1] == label:
                    labeled_markers[idx, -1] = label

    def label_markers(
        self,
        image: np.ndarray,
        markers: np.ndarray,
        view_type: ViewType,
        visualize: bool = False,
    ) -> np.ndarray:
        """
        Label markers based on view type alignment.
        """
        if len(markers) == 0:
            return np.empty((0, 3), dtype=object)
        logging.info("Labeling markers for view type: %s", view_type.name)

        height, width = image.shape[:2]

        # Configs for visualization
        vert_config = None
        horiz_config = None
        angle_config = None

        # Initialize labeled markers array
        labeled_markers = markers.copy()

        if view_type == ViewType.BACK_TOP:
            # Filter and label vertical markers
            vert_selected, vert_labels, vert_config = self._filter_back_top_vertical_markers(
                markers, width
            )
            self._assign_labels(markers, vert_selected, vert_labels, labeled_markers)

            # Filter and label horizontal markers
            horiz_selected, horiz_labels, horiz_config = self._filter_back_top_horizontal_markers(
                markers, height
            )
            self._assign_labels(markers, horiz_selected, horiz_labels, labeled_markers)
        elif view_type == ViewType.FRONT:
            selected, labels, angle_config = self._filter_front_markers(markers, width, 0.05, 5.0)
            self._assign_labels(markers, selected, labels, labeled_markers)
        elif view_type == ViewType.BACK_RIGHT:
            selected, labels, angle_config = self._filter_back_side_markers(
                markers, width, height, right=True
            )
            self._assign_labels(markers, selected, labels, labeled_markers)
        elif view_type == ViewType.BACK_LEFT:
            selected, labels, angle_config = self._filter_back_side_markers(
                markers, width, height, left=True
            )
            self._assign_labels(markers, selected, labels, labeled_markers)
        else:
            logging.warning("No labeling rules defined for view type: %s", view_type)

        if visualize:
            MarkerLabeler.visualize(image, labeled_markers, vert_config, horiz_config, angle_config)

        return labeled_markers

    @staticmethod
    def visualize(
        image: np.ndarray,
        labeled_markers: np.ndarray,
        vert_config: RegionConfig,
        horiz_config: RegionConfig,
        angle_config: RegionConfig,
    ) -> None:
        """
        Visualize markers and tolerance regions.
        """
        vis_image = image.copy()

        # Draw markers
        for marker in labeled_markers:
            x, y, _, label = marker

            if label is None:
                # Unlabeled: red circle
                cv2.circle(vis_image, (x, y), 8, (255, 0, 0), -1)
            else:
                # Labeled: green circle with text
                cv2.circle(vis_image, (x, y), 12, (0, 255, 0), -1)
                cv2.putText(
                    vis_image,
                    str(label),
                    (x + 10, y - 10),
                    cv2.FONT_HERSHEY_COMPLEX,
                    1.0,
                    (0, 0, 0),
                    2,
                    cv2.LINE_AA,
                )

        # Create figure
        # plt.figure(figsize=(12, 10))

        # Draw tolerance regions
        if vert_config:
            plt.axvline(
                vert_config.center,
                color="blue",
                linestyle="--",
                linewidth=1,
                alpha=0.25,
                label="Vertical center",
            )
            plt.axvspan(
                vert_config.center - vert_config.tolerance,
                vert_config.center + vert_config.tolerance,
                color="blue",
                alpha=0.1,
            )

        if horiz_config:
            plt.axhline(
                horiz_config.center,
                color="blue",
                linestyle="--",
                linewidth=1,
                alpha=0.25,
                label="Horizontal line",
            )
            plt.axhspan(
                horiz_config.center - horiz_config.tolerance,
                horiz_config.center + horiz_config.tolerance,
                color="blue",
                alpha=0.1,
            )

        if angle_config:
            # Draw angle line from center downwards
            radius = image.shape[0] // 2
            dx = np.cos(angle_config.angle) * radius
            dy = np.sin(angle_config.angle) * radius

            x_end_left = int(angle_config.center[0] - dx)
            y_end_left = int(angle_config.center[1] + dy)
            plt.plot(
                [angle_config.center[0], x_end_left],
                [angle_config.center[1], y_end_left],
                color="blue",
                linestyle="--",
                linewidth=1,
                alpha=0.25,
            )
            x_end_right = int(angle_config.center[0] + dx)
            y_end_right = int(angle_config.center[1] + dy)
            plt.plot(
                [angle_config.center[0], x_end_right],
                [angle_config.center[1], y_end_right],
                color="blue",
                linestyle="--",
                linewidth=1,
                alpha=0.25,
            )

        # plt.imshow(vis_image)
        # plt.axis("off")
        # plt.tight_layout()
        # plt.show()
        return vis_image
