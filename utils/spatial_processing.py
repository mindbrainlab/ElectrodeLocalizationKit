import vedo as vd
import numpy as np
import vtk
    
def compute_distance_between_coordinates(coordinates_1: np.ndarray, coordinates_2: np.ndarray):
    """Returns the distance between two electrodes."""
    return np.linalg.norm(coordinates_1-coordinates_2)
    
def normalize_mesh(mesh: vd.Mesh) -> float:
    """Scale Mesh average size to unit."""
    coords = mesh.points()
    coords = np.array(mesh.points())
    if not coords.shape[0]:
        return 1.0
    cm = np.mean(coords, axis=0)
    pts = coords - cm
    xyz2 = np.sum(pts * pts, axis=0)
    scale = 1 / np.sqrt(np.sum(xyz2) / len(pts))
    t = vtk.vtkTransform()
    t.PostMultiply()
    t.Scale(scale, scale, scale)
    tf = vtk.vtkTransformPolyDataFilter()
    tf.SetInputData(mesh.inputdata())
    tf.SetTransform(t)
    tf.Update()
    mesh.point_locator = None
    mesh.cell_locator = None
    mesh._update(tf.GetOutput())
    return scale

def rescale_to_original_size(mesh: vd.Mesh, scale: float) -> float:
    """Rescale Mesh to original size."""
    t = vtk.vtkTransform()
    t.PostMultiply()
    t.Scale(1/scale, 1/scale, 1/scale)
    tf = vtk.vtkTransformPolyDataFilter()
    tf.SetInputData(mesh.inputdata())
    tf.SetTransform(t)
    tf.Update()
    mesh.point_locator = None
    mesh.cell_locator = None
    mesh._update(tf.GetOutput())
    return 1.0

def compute_unit_spherical_coordinates_from_cartesian(cartesian_coordinates: list[float] | np.ndarray, origin = (0, 0, 0)) -> tuple[float, float]:
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

def compute_cartesian_coordinates_from_unit_spherical(spherical_coordinates: list[float] | tuple[float, float]) -> tuple[float, float, float]:
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

def compute_umeyama_transformation_matrix(source: np.ndarray,
                                          target: np.ndarray,
                                          rotate: bool = True,
                                          translate: bool = False) -> np.ndarray:
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
