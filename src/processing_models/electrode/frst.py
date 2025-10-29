import cv2
import numpy as np
from typing import List


class FRST:
    """
    Fast Radial Symmetry Transform (FRST) for circular pattern detection.

    Reference: https://ieeexplore.ieee.org/document/1217601
    """

    def run(
        self,
        image: np.ndarray,
        radii: List[int],
        alpha: float = 2.0,
        beta: float = 0.1,
    ) -> np.ndarray:
        """
        Run the FRST on an input grayscale image.
        """
        rows, cols = image.shape

        # --- Gradient computation ---
        grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
        grad_mag = np.hypot(grad_x, grad_y)
        grad_dir = np.arctan2(grad_y, grad_x)

        # --- Threshold gradients ---
        grad_mask = grad_mag > (beta * np.max(grad_mag))
        y_idx, x_idx = np.nonzero(grad_mask)  # indices of strong gradients

        # --- Accumulator ---
        S = np.zeros((rows, cols), dtype=np.float64)

        for radius in radii:
            # Projection images
            O_p = np.zeros((rows, cols), dtype=np.float64)
            O_n = np.zeros((rows, cols), dtype=np.float64)
            M_p = np.zeros((rows, cols), dtype=np.float64)
            M_n = np.zeros((rows, cols), dtype=np.float64)

            # Precompute cosine/sine for all valid points
            cos_dir = np.cos(grad_dir[y_idx, x_idx])
            sin_dir = np.sin(grad_dir[y_idx, x_idx])

            # Positive offsets (gradient points outward)
            x_p = (x_idx - radius * cos_dir).astype(int)
            y_p = (y_idx - radius * sin_dir).astype(int)

            # Negative offsets (gradient points inward)
            x_n = (x_idx + radius * cos_dir).astype(int)
            y_n = (y_idx + radius * sin_dir).astype(int)

            # Clip to image boundaries
            valid_p = (0 <= x_p) & (x_p < cols) & (0 <= y_p) & (y_p < rows)
            valid_n = (0 <= x_n) & (x_n < cols) & (0 <= y_n) & (y_n < rows)

            # Accumulate contributions
            np.add.at(O_p, (y_p[valid_p], x_p[valid_p]), 1)
            np.add.at(
                M_p,
                (y_p[valid_p], x_p[valid_p]),
                grad_mag[y_idx[valid_p], x_idx[valid_p]],
            )

            np.add.at(O_n, (y_n[valid_n], x_n[valid_n]), 1)
            np.add.at(
                M_n,
                (y_n[valid_n], x_n[valid_n]),
                grad_mag[y_idx[valid_n], x_idx[valid_n]],
            )

            # Symmetry contribution
            F_p = np.divide(M_p, O_p, out=np.zeros_like(M_p), where=O_p > 0)
            F_n = np.divide(M_n, O_n, out=np.zeros_like(M_n), where=O_n > 0)
            F = F_p - F_n

            # Gaussian smoothing (scale by radius)
            sigma = 0.25 * radius
            F_smooth = cv2.GaussianBlur(F, (0, 0), sigma)

            # Weighted accumulation
            S += np.power(F_smooth, alpha)

        # Normalize by number of radii
        return S / len(radii)
