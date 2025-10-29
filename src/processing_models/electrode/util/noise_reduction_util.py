import cv2
import numpy as np

from ..color_space import ColorSpace


class NoiseReductionUtil:

    @staticmethod
    def bilateral_filter(
        image: np.ndarray,
        diameter: int,
        sigma_color: float,
        sigma_space: float,
        border_type: int,
    ) -> np.ndarray:
        """
        Apply bilateral filter to reduce noise while preserving edges.

        Reference: https://homepages.inf.ed.ac.uk/rbf/CVonline/LOCAL_COPIES/MANDUCHI1/Bilateral_Filtering.html
        """
        # Apply bilateral filter
        return cv2.bilateralFilter(
            src=image,
            d=diameter,
            sigmaColor=sigma_color,
            sigmaSpace=sigma_space,
            borderType=border_type,
        )

    @staticmethod
    def guided_filter(
        image: np.ndarray,
        radius: int,
        epsilon: float,
        color_space: ColorSpace,
    ) -> np.ndarray:
        """
        Apply guided filter for edge-preserving smoothing.

        References: https://link.springer.com/chapter/10.1007/978-3-642-15549-9_1
        """
        # Default guidance boost
        guidance_boost = {"r": 1.0, "g": 1.3, "b": 1.0}

        # Convert image to float32 for processing
        image_float = image.astype(np.float32) / 255.0

        # Create guidance image with optional channel boosting
        def _create_guidance(img: np.ndarray) -> np.ndarray:
            guidance = img.copy()
            guidance[:, :, 0] *= guidance_boost["r"]
            guidance[:, :, 1] *= guidance_boost["g"]
            guidance[:, :, 2] *= guidance_boost["b"]
            return np.clip(guidance, 0, 1)

        # Filtering method selection
        if color_space == ColorSpace.RGB:
            # Convert to LAB for filtering
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB).astype(np.float32)

            # Create guidance image
            guide_rgb = _create_guidance(image_float)
            gray_guide = (
                0.1 * guide_rgb[:, :, 0] + 0.8 * guide_rgb[:, :, 1] + 0.1 * guide_rgb[:, :, 2]
            )

            # Normalize LAB channels
            l = lab[:, :, 0] / 255.0
            a = (lab[:, :, 1] + 128) / 255.0
            b = (lab[:, :, 2] + 128) / 255.0

            # Apply guided filter with different epsilon for each channel
            l_filtered = cv2.ximgproc.guidedFilter(gray_guide, l, radius, epsilon)
            a_filtered = cv2.ximgproc.guidedFilter(gray_guide, a, radius, epsilon * 1.5)
            b_filtered = cv2.ximgproc.guidedFilter(gray_guide, b, radius, epsilon * 1.5)

            # Reconstruct LAB image
            lab_filtered = np.zeros_like(lab)
            lab_filtered[:, :, 0] = l_filtered * 255.0
            lab_filtered[:, :, 1] = a_filtered * 255.0 - 128
            lab_filtered[:, :, 2] = b_filtered * 255.0 - 128

            return cv2.cvtColor(lab_filtered.astype(np.uint8), cv2.COLOR_LAB2RGB)

        elif color_space == ColorSpace.LAB:
            # Convert to LAB
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB).astype(np.float32)

            # Normalize channels
            l = lab[:, :, 0] / 255.0
            a = (lab[:, :, 1] + 128) / 255.0
            b = (lab[:, :, 2] + 128) / 255.0

            # Apply guided filter with different parameters
            l_filtered = cv2.ximgproc.guidedFilter(l, l, radius, epsilon)
            a_filtered = cv2.ximgproc.guidedFilter(a, a, radius, epsilon * 1.5)
            b_filtered = cv2.ximgproc.guidedFilter(b, b, radius, epsilon * 1.5)

            # Reconstruct LAB image
            lab_filtered = np.zeros_like(lab)
            lab_filtered[:, :, 0] = l_filtered * 255.0
            lab_filtered[:, :, 1] = a_filtered * 255.0 - 128
            lab_filtered[:, :, 2] = b_filtered * 255.0 - 128

            return cv2.cvtColor(lab_filtered.astype(np.uint8), cv2.COLOR_LAB2RGB)

        elif color_space == ColorSpace.GRAY:
            # Create guidance image with green channel boost
            guidance = _create_guidance(image_float)
            gray_guide = (
                0.2126 * guidance[:, :, 0] + 0.7152 * guidance[:, :, 1] + 0.0722 * guidance[:, :, 2]
            )

            # Filter each channel
            result = np.zeros_like(image_float)
            for i in range(3):
                result[:, :, i] = cv2.ximgproc.guidedFilter(
                    gray_guide, image_float[:, :, i], radius, epsilon
                )

            return (result * 255).astype(np.uint8)

        else:
            # Apply guided filter to each channel
            result = np.zeros_like(image_float)
            for i in range(3):
                result[:, :, i] = cv2.ximgproc.guidedFilter(
                    image_float[:, :, i], image_float[:, :, i], radius, epsilon
                )

            return (result * 255).astype(np.uint8)

    @staticmethod
    def nlm_denoising(
        image: np.ndarray,
        filtering_strength: float,
        color_space: ColorSpace,
    ) -> np.ndarray:
        """
        Apply Non-Local Means denoising with adaptive channel processing.

        Reference: https://www.ipol.im/pub/art/2011/bcm_nlm/article.pdf
        """
        # Perform channel-wise denoising
        if color_space == ColorSpace.RGB:
            # Default channel strength scaling
            channel_strengths = {
                "r": 1.0,  # Red channel full strength
                "g": 0.7,  # Green channel slightly reduced
                "b": 1.0,  # Blue channel full strength
            }

            # Split RGB channels
            r, g, b = cv2.split(image)

            # Denoise each channel with scaled strength
            r_denoised = cv2.fastNlMeansDenoising(
                r, None, filtering_strength * channel_strengths["r"]
            )
            g_denoised = cv2.fastNlMeansDenoising(
                g, None, filtering_strength * channel_strengths["g"]
            )
            b_denoised = cv2.fastNlMeansDenoising(
                b, None, filtering_strength * channel_strengths["b"]
            )

            # Merge denoised channels
            return cv2.merge((r_denoised, g_denoised, b_denoised))

        elif color_space == ColorSpace.LAB:
            # Default channel strength scaling
            channel_strengths = {
                "l": 1.0,  # Luminance full strength
                "a": 0.7,  # Color-a channel reduced
                "b": 0.7,  # Color-b channel reduced
            }

            # Convert to LAB color space
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)

            # Split LAB channels
            l, a, b = cv2.split(lab)

            # Denoise each channel with scaled strength
            l_denoised = cv2.fastNlMeansDenoising(
                l, None, filtering_strength * channel_strengths["l"]
            )
            a_denoised = cv2.fastNlMeansDenoising(
                a, None, filtering_strength * channel_strengths["a"]
            )
            b_denoised = cv2.fastNlMeansDenoising(
                b, None, filtering_strength * channel_strengths["b"]
            )

            # Merge denoised channels
            lab_denoised = cv2.merge((l_denoised, a_denoised, b_denoised))

            # Convert back to RGB color space
            return cv2.cvtColor(lab_denoised, cv2.COLOR_LAB2RGB)

        else:
            raise ValueError(f"NLM denoising not supported for {color_space} color space.")
