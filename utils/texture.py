import cv2 as cv
import numpy as np

from config.colors import HOUGH_CIRCLES_COLOR

# Hough circle detection functions
def compute_hough_circles(color_image, dog_image,
                          param1: float, param2: float,
                          min_distance_between_circles: int,
                          min_radius: int, max_radius: int,
                          rgb_circles_color: tuple[int, int, int] = HOUGH_CIRCLES_COLOR) -> tuple[np.ndarray, list[np.uint16] | None]:
    """Compute circles on the difference of gaussians (DoG) image using Hough circle detection."""    
    
    circles = cv.HoughCircles(dog_image,
                                cv.HOUGH_GRADIENT, 1, minDist=min_distance_between_circles,
                                param1=param1, param2=param2,
                                minRadius=min_radius, maxRadius=max_radius)

    circles_image = color_image.copy()
    if circles is not None:
        circles = np.uint16(np.around(circles))                                  # type: ignore
        for i in circles[0, :]:                                                  # type: ignore
            center = (i[0], i[1])
            radius = i[2]
            cv.circle(circles_image, center, radius, rgb_circles_color, -1)
            
    return (circles_image, circles)                                              # type: ignore

# Difference of Gaussians (DoG) texture processing functions
def compute_difference_of_gaussians(image: np.ndarray,
                                    ksize: int, sigma: float, F: float,
                                    threshold_level: int) -> np.ndarray:
    """Compute difference of gaussians (DoG) image."""
    
    dog_kernel = compute_dog_kernel(ksize, sigma, F)
    gray = rgb2gray(image)
    dog = cv.filter2D(src=gray, ddepth=-1, kernel=dog_kernel)
    
    return gray2binary(dog, threshold_level)

def compute_dog_kernel(ksize: int, sigma: float, F: float) -> np.ndarray:
    """Compute difference of gaussians (DoG) kernel."""
    
    # get gaussian kernel 1
    k1_1d = cv.getGaussianKernel(ksize, sigma)
    k1 = np.dot(k1_1d, k1_1d.T)
    
    # get gaussian kernel 2
    k2_1d = cv.getGaussianKernel(ksize, sigma*F)
    k2 = np.dot(k2_1d, k2_1d.T)
    
    # calculate difference of gaussians
    return k2 - k1

# Color conversion functions
def rgb2gray(rgb_image: np.ndarray) -> np.ndarray:
    """Convert RGB image to grayscale."""
    
    return cv.cvtColor(rgb_image, cv.COLOR_BGR2GRAY)

def gray2binary(image: np.ndarray, level: int) -> np.ndarray:
    """Convert grayscale image to binary image."""
    
    image[image < level] = 0
    image[image > level] = 255
    return image

def get_vertex_from_pixels(self, pixels, mesh, image_size):
    # Helper function to get the vertex from the mesh that corresponds to
    # the pixel coordinates
    #
    # Written by: Aleksij Kraljic, October 29, 2023
    
    # extract the vertices from the mesh
    vertices = mesh.points()
    
    # extract the uv coordinates from the mesh
    uv = mesh.pointdata['material_0']
    
    # convert pixels to uv coordinates
    uv_image = [(pixels[0]+0.5)/image_size[0],
                1-(pixels[1]+0.5)/image_size[1]]
    
    # find index of closest point in uv with uv_image
    uv_idx = np.argmin(np.linalg.norm(uv-uv_image, axis=1))
    
    return vertices[uv_idx]