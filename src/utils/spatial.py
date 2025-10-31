import numpy as np


def compute_distance_between_coordinates(coordinates_1: np.ndarray, coordinates_2: np.ndarray):
    """Returns the distance between two electrodes."""
    return np.linalg.norm(coordinates_1 - coordinates_2)


def compute_unit_spherical_coordinates_from_cartesian(
    cartesian_coordinates: list[float] | np.ndarray, origin=(0, 0, 0)
) -> tuple[float, float]:
    """
    Computes the spherical coordinates from the cartesian coordinates.
    Modeled after Matlab's cart2sph function.
    """
    x = cartesian_coordinates[0] - origin[0]
    y = cartesian_coordinates[1] - origin[1]
    z = cartesian_coordinates[2] - origin[2]
    hypotxy = np.hypot(x, y)
    phi = np.arctan2(z, hypotxy)
    theta = np.arctan2(y, x)
    return (theta, phi)


def compute_cartesian_coordinates_from_unit_spherical(
    spherical_coordinates: list[float] | tuple[float, float],
) -> tuple[float, float, float]:
    """
    Computes the cartesian coordinates from the spherical coordinates.
    Modeled after Matlab's sph2cart function.
    """
    theta = spherical_coordinates[0]
    phi = spherical_coordinates[1]

    z = 1 * np.sin(phi)
    rcosphi = 1 * np.cos(phi)
    x = rcosphi * np.cos(theta)
    y = rcosphi * np.sin(theta)
    return (x, y, z)


def compute_umeyama_transformation_matrix(
    source: np.ndarray, target: np.ndarray, rotate: bool = True, translate: bool = False
) -> np.ndarray:
    """
    Aligns two point clouds using the Umeyama algorithm. Transforms the source
    point cloud to the target point cloud.
    """
    # check if the point clouds have the same number of points and at least 3 points
    assert source.shape[0] == target.shape[0]
    assert source.shape[0] >= 3

    # compute centroids
    mu_s = np.mean(source, axis=0)
    mu_t = np.mean(target, axis=0)

    # center the point clouds
    source_centered = source - mu_s
    target_centered = target - mu_t

    # compute covariance matrix
    H = np.dot(source_centered.T, target_centered)

    # compute SVD
    U, _, Vt = np.linalg.svd(H)

    # compute rotation
    R = np.dot(Vt.T, U.T)

    # compute translation
    t = mu_t - np.dot(R, mu_s)

    # compute transformation matrix
    T = np.eye(4)
    if rotate:
        T[:3, :3] = R

    if translate:
        T[:3, 3] = t

    return T


def compute_angular_distance(vector_a: np.ndarray, vector_b: np.ndarray) -> float:
    """
    Computes the angular distance between two vectors in cartesian coordinates.
    TODO: Implement the function to compute the angular distance between two vectors in spherical coordinates.
    """
    val = np.dot(vector_a, vector_b) / (np.linalg.norm(vector_a) * np.linalg.norm(vector_b))
    if abs(val) > 1:
        val = 1 if val > 0 else -1

    return np.arccos(val)


def compute_rotation_axis(vector_a: np.ndarray, vector_b: np.ndarray) -> np.ndarray:
    # compute the rotation axis between the source and target vectors
    e = np.cross(vector_a, vector_b)
    if any(e):
        e = e / np.linalg.norm(e)
    return e


def align_vectors(
    input_vector,
    rotation_axis: np.ndarray,
    rotation_angle: float,
    attenuation: float = 1,
):
    # compute the rotation axis between the source and target vectors
    e = rotation_axis

    # theta - rotation angle
    theta = rotation_angle * attenuation

    # Q - rotation quaternion
    Q = (
        np.cos(theta / 2),
        e[0] * np.sin(theta / 2),
        e[1] * np.sin(theta / 2),
        e[2] * np.sin(theta / 2),
    )

    R = convert_quaternion_to_rotation_matrix(Q)

    output_vector = (R @ input_vector.T).T
    return output_vector


def convert_quaternion_to_rotation_matrix(Q: tuple[float, float, float, float]) -> np.ndarray:
    # w, x, y, z - quaternion components
    w = Q[0]
    x = Q[1]
    y = Q[2]
    z = Q[3]

    # rotation matrix components
    Rxx = 1 - 2 * (y**2 + z**2)
    Rxy = 2 * (x * y - z * w)
    Rxz = 2 * (x * z + y * w)
    Ryx = 2 * (x * y + z * w)
    Ryy = 1 - 2 * (x**2 + z**2)
    Ryz = 2 * (y * z - x * w)
    Rzx = 2 * (x * z - y * w)
    Rzy = 2 * (y * z + x * w)
    Rzz = 1 - 2 * (x**2 + y**2)
    R = np.array([[Rxx, Rxy, Rxz], [Ryx, Ryy, Ryz], [Rzx, Rzy, Rzz]])
    return R
