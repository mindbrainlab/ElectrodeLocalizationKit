import logging
import numpy as np

from vedo import Mesh, settings
from scipy.spatial import KDTree
from typing import Dict, List, Tuple


settings.default_backend = "vtk"
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class ElectrodeCurvatureDetector:
    def __init__(self, mesh: Mesh) -> None:
        """
        Detect electrode locations using curvature analysis and radial symmetry.
        """
        self.mesh_raw = mesh.clone()
        self.mesh = mesh.clone()
        self.vertices = self.mesh.points().copy()

        # Compute curvature (0 = Gaussian, 1 = Mean)
        self.mesh.compute_curvature(method=1)
        self.curvatures = self.mesh.pointdata["Mean_Curvature"]

        self.candidates = None
        self.filtered_curvatures = None
        self.saliency_map = None
        self.probability_map = None
        self.gradient_directions = None

    def _remove_extreme_curvatures(
        self,
        outlier_percentile_low: int = 5,
        outlier_percentile_high: int = 95,
        smoothing_iterations: int = 3,
    ) -> None:
        """
        Clip extreme curvature values and apply spatial smoothing.
        """
        curvatures = self.curvatures.copy()

        # Remove extreme outlier and cap values
        low_threshold = np.percentile(curvatures, outlier_percentile_low)
        high_threshold = np.percentile(curvatures, outlier_percentile_high)
        filtered_curvatures = np.clip(curvatures, low_threshold, high_threshold)

        # Apply spatial smoothing to reduce noise
        if smoothing_iterations > 0:
            tree = KDTree(self.vertices)
            for _ in range(smoothing_iterations):
                smoothed = filtered_curvatures.copy()
                for i, vertex in enumerate(self.vertices):
                    neighbor_indices = tree.query_ball_point(vertex, r=3.0)
                    if len(neighbor_indices) > 1:
                        smoothed[i] = np.median(filtered_curvatures[neighbor_indices])
                filtered_curvatures = smoothed

        self.filtered_curvatures = filtered_curvatures

    def _compute_local_curvature_std(self, radius: float = 8.0) -> np.ndarray:
        """
        Compute local curvature standard deviation for each vertex.
        """
        tree = KDTree(self.vertices)
        local_stds = np.zeros(len(self.vertices))

        for i, vertex in enumerate(self.vertices):
            neighbor_indices = tree.query_ball_point(vertex, radius)
            if len(neighbor_indices) > 3:
                neighbor_curvatures = self.curvatures[neighbor_indices]
                local_stds[i] = np.std(neighbor_curvatures)

        return local_stds

    def _create_head_region_mask(self) -> np.ndarray:
        """
        Create mask focusing on head region while excluding artifacts and high-variance areas.
        """
        curvatures = (
            self.filtered_curvatures if self.filtered_curvatures is not None else self.curvatures
        )

        # Start with all vertices
        mask = np.ones(len(self.vertices), dtype=bool)

        # Exclude remaining extreme curvature outliers
        curvature_threshold = np.percentile(np.abs(curvatures), 85)
        mask &= np.abs(curvatures) < curvature_threshold

        # Focus on relatively stable regions
        local_curvature_std = self._compute_local_curvature_std(radius=8.0)
        curvature_std_threshold = np.percentile(local_curvature_std, 90)
        mask &= local_curvature_std < curvature_std_threshold

        logging.info(
            "Head region mask includes %d / %d vertices (%.1f%%)",
            np.sum(mask),
            len(mask),
            np.sum(mask) / len(mask) * 100,
        )
        return mask

    def _compute_saliency_map(
        self,
        region_mask: np.ndarray,
        neighborhood_radius: float = 7.0,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute saliency map, probability map, and gradient directions.
        """
        vertices = self.vertices.copy()
        curvatures = (
            self.filtered_curvatures if self.filtered_curvatures is not None else self.curvatures
        )

        tree = KDTree(vertices)
        n_vertices = len(vertices)

        # Initialize maps
        saliency_scores = np.zeros(n_vertices)
        probability_map = np.zeros(n_vertices)
        gradient_directions = np.zeros((n_vertices, 3))  # 3D gradient directions

        # Only process vertices in the head region
        valid_indices = np.where(region_mask)[0]

        for i in valid_indices:
            vertex = vertices[i]
            current_curvature = curvatures[i]

            # Find local neighborhood
            neighbor_indices = tree.query_ball_point(vertex, neighborhood_radius)
            neighbor_indices = [idx for idx in neighbor_indices if region_mask[idx]]

            if len(neighbor_indices) < 5:
                continue

            neighbor_curvatures = curvatures[neighbor_indices]
            neighbor_positions = vertices[neighbor_indices]

            # Compute local saliency based on:
            # 1. Local curvature prominence
            local_mean = np.mean(neighbor_curvatures)
            local_std = np.std(neighbor_curvatures)

            if local_std > 0:
                prominence = (current_curvature - local_mean) / local_std
                saliency_scores[i] = max(0, prominence)  # Only positive prominences

            # 2. Compute gradient direction to local maximum
            if len(neighbor_indices) > 1:
                # Find direction to highest curvature neighbor
                max_neighbor_idx = neighbor_indices[np.argmax(neighbor_curvatures)]
                if max_neighbor_idx != i:
                    direction = vertices[max_neighbor_idx] - vertex
                    norm = np.linalg.norm(direction)
                    if norm > 0:
                        gradient_directions[i] = direction / norm

            # 3. Enhance based on local geometry (bump-like structures)
            if len(neighbor_indices) >= 8:
                # Check if current points is a local maximum
                is_local_max = current_curvature >= np.percentile(neighbor_curvatures, 75)

                # Compute radial symmetry score
                radial_positions = neighbor_positions - vertex
                distances = np.linalg.norm(radial_positions, axis=1)
                if len(distances) > 0 and np.std(distances) > 0:
                    # Prefer circular/symmetric arrangements
                    symmetry_score = 1.0 / (1.0 + np.std(distances) / np.mean(distances))
                    if is_local_max:
                        saliency_scores[i] *= 1.0 + symmetry_score

        # Normalize saliency scores
        if np.max(saliency_scores) > 0:
            saliency_scores /= np.max(saliency_scores)

        # Convert saliency to probablity usign sigmod-like function
        probability_map = 1.0 / (1.0 + np.exp(-5 * (saliency_scores - 0.3)))
        probability_map[~region_mask] = 0
        saliency_scores[~region_mask] = 0
        gradient_directions[~region_mask] = 0

        self.saliency_map = saliency_scores
        self.probability_map = probability_map
        self.gradient_directions = gradient_directions

        return saliency_scores, probability_map, gradient_directions

    def _detect_electrode_candidates(
        self,
        min_probability: float = 0.3,
        min_distance: float = 15.0,
    ) -> List[Dict[str, np.ndarray]]:
        """
        Detect electrode candidates using non-maximum suppression on probability map.
        """
        if self.probability_map is None:
            raise ValueError("Must compute saliency map first")

        # Find peaks in probability map
        high_prob_indices = np.where(self.probability_map > min_probability)[0]
        if len(high_prob_indices) == 0:
            return []

        # Sort by probabiilty
        sorted_indices = high_prob_indices[
            np.argsort(self.probability_map[high_prob_indices])[::-1]
        ]

        # Apply non-maximum suppression based on distance
        candidates = []
        for vertex_idx in sorted_indices:
            vertex_pos = self.vertices[vertex_idx]
            probability = self.probability_map[vertex_idx]
            direction = self.gradient_directions[vertex_idx]

            # Check if too close to existing candidates
            too_close = any(
                np.linalg.norm(vertex_pos - c["position"]) < min_distance for c in candidates
            )
            if not too_close:
                candidates.append(
                    {
                        "vertex_index": vertex_idx,
                        "position": vertex_pos,
                        "probability": probability,
                        "gradient_direction": direction,
                        "saliency": self.saliency_map[vertex_idx],
                    }
                )

        logging.info("Detected %d electrode candidates.", len(candidates))
        self.candidates = candidates
        return candidates

    def extract_curvatures(self):
        """
        Run the full electrode detection pipeline.
        """
        self._remove_extreme_curvatures()
        head_mask = self._create_head_region_mask()
        saliency, probability, directions = self._compute_saliency_map(
            region_mask=head_mask, neighborhood_radius=7
        )
        candidates = self._detect_electrode_candidates()

        return {
            "saliency_map": saliency,
            "probability_map": probability,
            "gradient_directions": directions,
            "candidates": candidates,
            "head_mask": head_mask,
        }
