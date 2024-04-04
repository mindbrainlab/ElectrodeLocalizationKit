from PyQt6.QtCore import QModelIndex, Qt, QAbstractTableModel
import numpy as np
import vedo as vd
from collections.abc import Iterable

from data.data_loader import load_electrodes_from_file

from .electrode import Electrode

class CapModel(QAbstractTableModel):
    """CapModel class for displaying a list of electrodes in a Qt application."""
    def __init__(self):
        super().__init__()
        self._data = []
        self._labels = []
        
        # define Electrode class attributes to display in the table
        self._display_keys = ('label', 'modality')
        
    def set_labels(self, labels: list) -> None: 
        self._labels = labels

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._display_keys)
    
    def get_electrode(self, index: int) -> Electrode:
        return self._data[index]
    
    def set_electrode_labeled_flag(self, index: int, labeled: bool) -> None:
        self._data[index].labeled = labeled
        
    def get_labeled_electrodes(self, modality: list[str]) -> list[Electrode]:
        return [electrode for electrode in self._data
                if electrode.labeled and electrode.modality in modality]
    
    def get_electrodes_by_modality(self, modality: list[str]) -> list[Electrode]:
        return [electrode for electrode in self._data if electrode.modality in modality]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole) -> str | None:
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                value = self._data[index.row()][self._display_keys[index.column()]]
                return str(value)
            
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole) -> str | None:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return str(self._display_keys[section])
        return super().headerData(section, orientation, role)

    def insert_electrode(self, electrode: Electrode, parent=QModelIndex()) -> None:
        self.beginInsertRows(parent, self.rowCount(), self.rowCount())
        self._data.append(electrode)
        self.endInsertRows()
            
    def compute_centroid(self):
        all_measured_electrodes = self.get_electrodes_by_modality(['scan', 'mri'])
        coordinates = [electrode.coordinates for electrode in all_measured_electrodes]
        centroid = np.mean(coordinates, axis=0) # type: ignore
        
        for electrode in all_measured_electrodes:
            electrode.cap_centroid = centroid
        
    def read_electrodes_from_file(self, filename: str) -> None:
        electrodes = load_electrodes_from_file(filename)
        for electrode in electrodes:
            self.insert_electrode(electrode)
    
    def remove_electrode(self, electrode_index, parent=QModelIndex()) -> None:
        self.beginRemoveRows(parent, self.rowCount(), self.rowCount())
        self._data.pop(electrode_index)
        self.endRemoveRows()
    
    def _calculate_distances(self, target_coordinates: Iterable[float], modality) -> list[tuple[int, float]]:
        """Calculates the distances between the given point and all points in the electrode cap."""
        distances = []
        for idx, electrode in enumerate(self._data):
            point = np.array(electrode.coordinates)
            dist =  np.linalg.norm(point-target_coordinates)
            distances.append((idx, dist))
        return distances    

    def remove_closest_electrode(self, target_coordinates: Iterable[float], modality: str) -> None:
        """Removes the point in the electrode cap closest to the given point."""
        distances = self._calculate_distances(target_coordinates, modality)
        
        # remove the point with the smallest distance
        if len(distances) > 0:
            min_distance = min(distances, key=lambda x: x[1])
            self.remove_electrode(min_distance[0])
            
    def transform_electrodes(self, modality: str, A: np.ndarray) -> None:
        """Applies a transformation to all electrodes in the cap."""
        for electrode in self._data:
            if electrode.modality == modality:
                electrode.create_coordinates_snapshot()
                electrode.apply_transformation(A)
                
    def project_electrodes_to_mesh(self, mesh: vd.Mesh, modality: str) -> None:
        """Projects all electrodes in the cap to the given mesh."""
        for electrode in self._data:
            if electrode.modality == modality:
                electrode.create_coordinates_snapshot()
                electrode.project_to_mesh(mesh)
                
    def undo_transformation(self) -> None:
        """Undoes the last transformation step."""
        for electrode in self._data:
            electrode.revert_coordinates_to_snapshot()

    def setData(self, index, value, role) -> bool:
        if role == Qt.ItemDataRole.EditRole:
            self._data[index.row()][self._display_keys[index.column()]] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index) -> Qt.ItemFlag:
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable
