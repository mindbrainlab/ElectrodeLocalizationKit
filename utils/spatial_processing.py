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