import logging
import numpy as np

from typing import List, Tuple
from scipy.spatial.distance import pdist, squareform

from .view_type import ViewType
from .detection_method import DetectionMethod


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class ElectrodeMerger:

    def __init__(self, distance_threshold: float = 15.0) -> None:
        """
        Initialize electrode clusterer to process and merge electrodes from multiple camera views.
        """
        self.distance_threshold = distance_threshold

    def _dfs_cluster_search(
        self,
        node: int,
        cluster: List[int],
        visited: List[bool],
        distance_matrix: np.ndarray,
        threshold: float,
    ) -> None:
        """
        Depth-first search to find connected components in a cluster.
        """
        visited[node] = True
        cluster.append(node)

        # Explore all neighbors within threshold distance
        for neighbor in range(len(distance_matrix)):
            if not visited[neighbor] and distance_matrix[node][neighbor] <= threshold:
                self._dfs_cluster_search(neighbor, cluster, visited, distance_matrix, threshold)

    def _find_clusters(self, distance_matrix: np.ndarray, threshold: float) -> List[List[int]]:
        """
        Find clusters using distance threshold with connected components approach.
        """
        if len(distance_matrix.shape) != 2 or distance_matrix.shape[0] != distance_matrix.shape[1]:
            raise ValueError("Distance matrix must be square")

        if threshold < 0:
            raise ValueError("Threshold must be non-negative")

        n = len(distance_matrix)
        visited = [False] * n
        clusters = []

        # Find all connected components (clusters)
        for i in range(n):
            if not visited[i]:
                cluster = []
                self._dfs_cluster_search(i, cluster, visited, distance_matrix, threshold)
                clusters.append(cluster)

        return clusters

    def _find_geometric_median(
        self, points: np.ndarray, max_iterations: int = 100, tolerance: float = 1e-6
    ) -> np.ndarray:
        """
        Find geometric median using Weiszfeld's algorithm.
        """
        points = np.array(points, dtype=np.float64)

        if len(points) == 1:
            return points[0]

        if len(points) == 2:
            return np.mean(points, axis=0)

        # Start with centroid as initial guess
        median = np.mean(points, axis=0)

        for _ in range(max_iterations):
            # Calculate distances from current median to all points
            distances = np.linalg.norm(points - median, axis=1)

            # Handle points that coincide with current median (avoid division by zero)
            non_zero_distances = distances > tolerance

            if not np.any(non_zero_distances):
                # All points are at the current median
                break

            # Calculate weights (inverse of distances)
            weights = np.zeros(len(points))
            weights[non_zero_distances] = 1.0 / distances[non_zero_distances]

            # Skip points that are too close to avoid numerical issues
            if np.sum(weights) == 0:
                break

            # Calculate new median as weighted average
            new_median = np.sum(weights[:, np.newaxis] * points, axis=0) / np.sum(weights)

            # Check for convergence
            if np.linalg.norm(new_median - median) < tolerance:
                break

            median = new_median

        return median

    def _compute_cluster_centroid(
        self,
        cluster_electrodes: List[Tuple[ViewType, DetectionMethod, float, float, float, str]],
    ) -> Tuple[ViewType, DetectionMethod, float, float, float, str]:
        """
        Compute centroid for a cluster with marker priority.
        """
        if len(cluster_electrodes) == 1:
            return cluster_electrodes[0]

        # Check if any electrode in cluster uses marker method
        marker_electrodes = [
            electrode for electrode in cluster_electrodes if electrode[1] == DetectionMethod.MARKER
        ]

        if len(marker_electrodes) > 0:
            # Find closest marker
            cluster_electrodes = marker_electrodes

        # Check if any electrode in cluster is labeled
        labeled_electrodes = [
            electrode
            for electrode in cluster_electrodes
            if electrode[5] != "" and electrode[5] is not None
        ]

        if len(labeled_electrodes) > 0:
            # Find closest labeled electrode
            cluster_electrodes = labeled_electrodes

        # Find geometric median of all points and return closest electrode
        all_coords = np.array([(x, y, z) for _, _, x, y, z, _ in cluster_electrodes])
        geometric_median = self._find_geometric_median(all_coords)

        # Find closest actual electrode to geometric median
        distances = np.linalg.norm(all_coords - geometric_median, axis=1)
        closest_idx = np.argmin(distances)

        return cluster_electrodes[closest_idx]

    def cluster_electrodes(
        self,
        electrodes: List[Tuple[ViewType, DetectionMethod, float, float, float, str]],
    ) -> List[Tuple[ViewType, DetectionMethod, float, float, float, str]]:
        """
        Cluster nearby electrodes and compute centroids with labeled MARKER method priority.
        """
        # Extract coordinates and create metadata mapping
        coordinates = np.array([[x, y, z] for _, _, x, y, z, _ in electrodes])

        # Compute pairwise distances
        distances = squareform(pdist(coordinates, metric="euclidean"))

        # Find clusters using distance threshold
        clusters = self._find_clusters(distances, self.distance_threshold)
        logging.info(f"Detected {len(clusters)} electrode clusters")

        # Compute centroids for each cluster
        centroids = []
        for cluster_indices in clusters:
            cluster_electrodes = [electrodes[i] for i in cluster_indices]
            centroid = self._compute_cluster_centroid(cluster_electrodes.copy())
            centroids.append(centroid)
        logging.info(f"Electrodes merged, reduced count from {len(electrodes)} to {len(centroids)}")

        return np.array(centroids)
