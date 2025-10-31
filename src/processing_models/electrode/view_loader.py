import cv2
import os
import logging
import numpy as np
import matplotlib.pyplot as plt

from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional, Union

from .view_type import ViewType
from .params import ProcessingParams
from .marker_labeler import MarkerLabeler
from .marker_detector import MarkerDetector
from .detection_method import DetectionMethod
from .electrode_detector import ElectrodeDetector
from .basic_electrode_detector import BasicElectrodeDetector
from concurrent.futures import ProcessPoolExecutor, as_completed
from .util import BackgroundMaskUtil, IlluminationCorrectionUtil, NoiseReductionUtil


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class ViewLoader:
    def __init__(
        self,
        views_path: Union[str, Path],
        params: Optional[ProcessingParams] = None,
    ) -> None:
        """
        Initialize view loader for working with 2d images of 3d head scans.
        """
        self.metadata = {}
        self.images = self._load_images(views_path)
        self.images_raw = self.images.copy()
        self.preprocessed = {}
        self.detected = defaultdict(dict)
        self.params = params or ProcessingParams()

        if params is not None:
            # Avoid preprocessing data in util tests
            self.preprocess_data()

    def _load_images(self, views_path: Union[str, Path]) -> Dict[ViewType, np.ndarray]:
        """
        Load a set of 2d views each captured from different engle.
        """
        if not os.path.exists(views_path):
            logging.error(f"Views folder not found: {views_path}")
            return None
        logging.info(f"Loading views from {views_path}")

        # Find images for each view type
        images = {}
        for view_type in ViewType:
            image_path = f"{views_path}/{view_type.name}.png"
            image = cv2.imread(image_path)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            images[view_type] = image

            # Store metadata
            self.metadata[view_type] = {
                "path": image_path,
                "shape": image.shape,
                "dtype": str(image.dtype),
            }
            logging.info(f"Loaded {view_type.name}: {image.shape}")

        return images

    def preprocess_data(self) -> None:
        """
        Comprehensive preprocessing for all loaded images.
        """
        if self.images is None:
            raise ValueError("Views not loded")
        logging.info("Preprocessign data...")

        for view_type, image in self.images.items():
            # Basic preprocessing (common for all methods)
            logging.info(f"Preprocessing {view_type.name}...")
            preprocessed_variants = {"original_image": image.copy()}

            # Resize
            preprocessed_image = cv2.resize(
                image, self.params.target_size, interpolation=cv2.INTER_AREA
            )

            # Color constancy (Gray World assumption)
            if self.params.gray_world:
                preprocessed_float = preprocessed_image.astype(np.float32)
                avg_b = np.mean(preprocessed_float[:, :, 0])
                avg_g = np.mean(preprocessed_float[:, :, 1])
                avg_r = np.mean(preprocessed_float[:, :, 2])

                avg_gray = (avg_b + avg_g + avg_r) / 3.0

                if avg_b > 0:
                    preprocessed_float[:, :, 0] *= avg_gray / avg_b
                if avg_g > 0:
                    preprocessed_float[:, :, 1] *= avg_gray / avg_g
                if avg_r > 0:
                    preprocessed_float[:, :, 2] *= avg_gray / avg_r

                preprocessed_image = np.clip(preprocessed_float, 0, 255).astype(np.uint8)

            # Noise reduction
            if self.params.bilateral.enabled:
                preprocessed_image = NoiseReductionUtil.bilateral_filter(
                    preprocessed_image,
                    self.params.bilateral.diameter,
                    self.params.bilateral.sigma_color,
                    self.params.bilateral.sigma_space,
                    self.params.bilateral.border_type,
                )
            if self.params.guided.enabled:
                preprocessed_image = NoiseReductionUtil.guided_filter(
                    preprocessed_image,
                    self.params.guided.radius,
                    self.params.guided.epsilon,
                    self.params.guided.color_space,
                )
            if self.params.nlm.enabled:
                preprocessed_image = NoiseReductionUtil.nlm_denoising(
                    preprocessed_image,
                    self.params.nlm.filtering_strength,
                    self.params.nlm.color_space,
                )

            # Illumination correction
            if self.params.clahe.enabled:
                preprocessed_image = IlluminationCorrectionUtil.clahe_equalization(
                    preprocessed_image,
                    self.params.clahe.clip_limit,
                    self.params.clahe.tile_grid_size,
                    self.params.clahe.color_space,
                )

            # Background mask generation
            background_mask = BackgroundMaskUtil.generate_background_mask(
                preprocessed_image, None, (25, 25)
            )
            preprocessed_variants["background_mask"] = background_mask.copy()
            preprocessed_variants["foreground_mask"] = cv2.bitwise_not(background_mask).copy()

            # Set white background to preprocessed image
            mask = background_mask.astype(bool)
            preprocessed_image[mask] = [255, 255, 255]

            # Normalization
            if self.params.normalize:
                preprocessed_image = preprocessed_image.astype(np.float32) / 255.0

            preprocessed_variants["preprocessed_image"] = preprocessed_image.copy()
            self.preprocessed[view_type] = preprocessed_variants.copy()

    def detect_markers(
        self,
        view_types: Optional[List[ViewType]] = None,
        methods: Optional[List[DetectionMethod]] = None,
    ) -> None:
        """
        Detects markers in preprocessed images for given view types.
        """
        if not self.preprocessed:
            raise ValueError("View images are not preprocessed")

        if not view_types:
            view_types = [view_type for view_type in ViewType if view_type.marker_cfg is not None]

        if not methods:
            methods = [DetectionMethod.TRADITIONAL, DetectionMethod.FRST]

        logging.info("Detecting markers for view types: %s", [vt.name for vt in view_types])

        detector = MarkerDetector()
        for view_type in view_types:
            markers, _ = detector.detect(
                self.preprocessed[view_type]["preprocessed_image"].copy(),
                self.preprocessed[view_type]["foreground_mask"].copy(),
                view_type,
                methods,
            )
            markers_image = MarkerDetector.draw_circles(
                self.preprocessed[view_type]["original_image"].copy(), markers
            )

            markers = markers.squeeze(0).copy()
            markers = np.column_stack((markers, np.array([None] * markers.shape[0], dtype=object)))
            self.detected[view_type][DetectionMethod.MARKER] = markers.copy()
            self.preprocessed[view_type]["markers"] = markers.copy()
            self.preprocessed[view_type]["markers_image"] = markers_image.copy()

    def label_markers(
        self,
        view_types: Optional[List[ViewType]] = None,
    ) -> None:
        """
        Labels markers in preprocessed images for given view types.
        """
        if not self.preprocessed:
            raise ValueError("View images are not preprocessed")

        if not view_types:
            view_types = [view_type for view_type in ViewType if view_type.marker_cfg is not None]

        logging.info("Labeling markers for view types: %s", [vt.name for vt in view_types])

        labeler = MarkerLabeler()
        for view_type in view_types:
            if "markers" not in self.preprocessed[view_type]:
                logging.warning(f"No markers detected for {view_type.name}, skipping labeling.")
                continue

            labeled_markers = labeler.label_markers(
                self.preprocessed[view_type]["original_image"].copy(),
                self.preprocessed[view_type]["markers"].copy(),
                view_type,
                visualize=False,
            )
            self.detected[view_type][DetectionMethod.MARKER] = labeled_markers.copy()
            self.preprocessed[view_type]["labeled_markers"] = labeled_markers.copy()

    def detect_electrodes_basic(
        self,
        view_types: Optional[List[ViewType]] = None,
        methods: Optional[List[DetectionMethod]] = None,
    ) -> None:
        """
        Detects electrodes in preprocessed images for given view types.
        """
        if not self.preprocessed:
            raise ValueError("View images are not preprocessed")

        if not view_types:
            view_types = [view_type for view_type in ViewType if view_type.marker_cfg is not None]

        if not methods:
            methods = [DetectionMethod.TRADITIONAL, DetectionMethod.FRST]

        logging.info(
            "Detecting electrodes (basic) for view types: %s", [vt.name for vt in view_types]
        )

        detector = BasicElectrodeDetector()
        for view_type in view_types:
            electrodes, _ = detector.detect(
                self.preprocessed[view_type]["preprocessed_image"].copy(),
                self.preprocessed[view_type]["foreground_mask"].copy(),
                view_type,
                methods,
            )
            electrodes_image = BasicElectrodeDetector.draw_circles(
                self.preprocessed[view_type]["original_image"].copy(), electrodes
            )

            electrodes = electrodes.squeeze(0).copy()
            electrodes = np.column_stack(
                (electrodes, np.array([None] * electrodes.shape[0], dtype=object))
            )
            self.detected[view_type][DetectionMethod.ELECTRODE_BASIC] = electrodes.copy()
            self.preprocessed[view_type]["electrodes_basic"] = electrodes.copy()
            self.preprocessed[view_type]["electrodes_basic_image"] = electrodes_image.copy()

    def detect_electrodes(
        self,
        view_types: Optional[List[ViewType]] = None,
    ) -> None:
        """
        Detects electrodes in preprocessed images for given view types.
        """
        if not self.preprocessed:
            raise ValueError("View images are not preprocessed")

        if not view_types:
            view_types = [view_type for view_type in ViewType if view_type.marker_cfg is not None]

        logging.info("Detecting electrodes for view types: %s", [vt.name for vt in view_types])

        detector = ElectrodeDetector()
        for view_type in view_types:
            electrodes, _, _ = detector.detect(
                self.preprocessed[view_type]["preprocessed_image"].copy(),
                self.preprocessed[view_type]["foreground_mask"].copy(),
                view_type,
            )
            electrodes_image = BasicElectrodeDetector.draw_circles(
                self.preprocessed[view_type]["original_image"].copy(), electrodes
            )

            electrodes = electrodes.squeeze(0).copy()
            electrodes = np.column_stack(
                (electrodes, np.array([None] * electrodes.shape[0], dtype=object))
            )
            self.detected[view_type][DetectionMethod.ELECTRODE] = electrodes.copy()
            self.preprocessed[view_type]["electrodes"] = electrodes.copy()
            self.preprocessed[view_type]["electrodes_image"] = electrodes_image.copy()

    @staticmethod
    def detect_markers_per_view(
        view_type: ViewType,
        methods: List[DetectionMethod],
        preprocessed_entry: Dict[str, np.ndarray],
    ):
        """
        Run marker detection for one view type.
        """
        detector = MarkerDetector()
        markers, _ = detector.detect(
            preprocessed_entry["preprocessed_image"].copy(),
            preprocessed_entry["foreground_mask"].copy(),
            view_type,
            methods,
        )
        markers_image = MarkerDetector.draw_circles(
            preprocessed_entry["original_image"].copy(), markers
        )
        markers = markers.squeeze(0).copy()
        markers = np.column_stack((markers, np.array([None] * markers.shape[0], dtype=object)))
        return ("marker", view_type, markers, markers_image)

    @staticmethod
    def detect_basic_electrodes_per_view(
        view_type: ViewType,
        methods: List[DetectionMethod],
        preprocessed_entry: Dict[str, np.ndarray],
    ):
        """
        Run basic electrode detection for one view type.
        """
        detector = BasicElectrodeDetector()
        electrodes, _ = detector.detect(
            preprocessed_entry["preprocessed_image"].copy(),
            preprocessed_entry["foreground_mask"].copy(),
            view_type,
            methods,
        )
        electrodes_image = BasicElectrodeDetector.draw_circles(
            preprocessed_entry["original_image"].copy(), electrodes
        )
        electrodes = electrodes.squeeze(0).copy()
        electrodes = np.column_stack(
            (electrodes, np.array([None] * electrodes.shape[0], dtype=object))
        )
        return ("electrode_basic", view_type, electrodes, electrodes_image)

    @staticmethod
    def detect_advanced_electrodes_per_view(
        view_type: ViewType,
        preprocessed_entry: Dict[str, np.ndarray],
    ):
        """
        Run advanced electrode detection for one view type.
        """
        detector = ElectrodeDetector()
        electrodes, _, _ = detector.detect(
            preprocessed_entry["preprocessed_image"].copy(),
            preprocessed_entry["foreground_mask"].copy(),
            view_type,
        )
        electrodes_image = BasicElectrodeDetector.draw_circles(
            preprocessed_entry["original_image"].copy(), electrodes
        )
        electrodes = electrodes.squeeze(0).copy()
        electrodes = np.column_stack(
            (electrodes, np.array([None] * electrodes.shape[0], dtype=object))
        )
        return ("electrode_advanced", view_type, electrodes, electrodes_image)

    def detect_markers_and_electrodes(
        self,
        view_types: Optional[List[ViewType]] = None,
        methods: Optional[List[DetectionMethod]] = None,
    ) -> None:
        """
        Detects markers and electrodes in preprocessed images for given view types.
        """
        if not self.preprocessed:
            raise ValueError("View images are not preprocessed")

        if not view_types:
            view_types = [view_type for view_type in ViewType if view_type.marker_cfg is not None]

        if not methods:
            methods = [DetectionMethod.TRADITIONAL, DetectionMethod.FRST]

        logging.info(
            "Detecting markers and electrodes for view types: %s", [vt.name for vt in view_types]
        )

        with ProcessPoolExecutor() as executor:
            futures = {}

            for view_type in view_types:
                preprocessed_entry = self.preprocessed[view_type]

                # Submit all three detectors as separate processes per view type
                futures[
                    executor.submit(
                        ViewLoader.detect_markers_per_view,
                        view_type,
                        methods,
                        preprocessed_entry,
                    )
                ] = (view_type, "marker")

                futures[
                    executor.submit(
                        ViewLoader.detect_basic_electrodes_per_view,
                        view_type,
                        methods,
                        preprocessed_entry,
                    )
                ] = (view_type, "electrode_basic")

                futures[
                    executor.submit(
                        ViewLoader.detect_advanced_electrodes_per_view,
                        view_type,
                        preprocessed_entry,
                    )
                ] = (view_type, "electrode_advanced")

            # Collect results
            for future in as_completed(futures):
                result_type, view_type, data, image = future.result()

                if result_type == "marker":
                    self.detected[view_type][DetectionMethod.MARKER] = data.copy()
                    self.preprocessed[view_type]["markers"] = data.copy()
                    self.preprocessed[view_type]["markers_image"] = image.copy()

                elif result_type == "electrode_basic":
                    self.detected[view_type][DetectionMethod.ELECTRODE_BASIC] = data.copy()
                    self.preprocessed[view_type]["electrodes_basic"] = data.copy()
                    self.preprocessed[view_type]["electrodes_basic_image"] = image.copy()

                elif result_type == "electrode_advanced":
                    self.detected[view_type][DetectionMethod.ELECTRODE] = data.copy()
                    self.preprocessed[view_type]["electrodes"] = data.copy()
                    self.preprocessed[view_type]["electrodes_image"] = image.copy()

    def visualize(
        self,
        view_types: Optional[List[ViewType]] = None,
        show_markers: bool = True,
        show_electrodes: bool = True,
    ) -> None:
        """
        Visualize original, preprocessed, markers, and electrodes images for each selected view type. Each view type is shown in a new row.
        """
        if not self.preprocessed:
            raise ValueError("No preprocessed images available.")

        if not view_types:
            view_types = list(self.preprocessed.keys())

        # Build column setup
        columns = [
            ("original_image", "Original"),
            ("preprocessed_image", "Preprocessed"),
        ]
        if show_markers:
            columns.append(("markers_image", "Markers"))
        if show_electrodes:
            columns.append(("electrodes_basic_image", "Electrodes (basic)"))
            columns.append(("electrodes_image", "Electrodes"))

        n_rows = len(view_types)
        n_cols = len(columns)

        fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))

        # Ensure axes is 2D for consistent indexing
        if n_rows == 1:
            axes = [axes]
        else:
            axes = axes.tolist()

        for row_idx, view_type in enumerate(view_types):
            for col_idx, (key, title) in enumerate(columns):
                ax = axes[row_idx][col_idx] if n_rows > 1 else axes[0][col_idx]
                img = self.preprocessed[view_type].get(key)

                if img is not None:
                    ax.imshow(img, cmap="gray" if img.ndim == 2 else None)
                    ax.set_title(f"{view_type.name} - {title}")
                else:
                    ax.set_title(f"{view_type.name} - {title} (missing)")
                ax.axis("off")

        plt.tight_layout()
        plt.show()
