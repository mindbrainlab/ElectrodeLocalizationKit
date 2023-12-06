from PyQt6.QtCore import QModelIndex, Qt, QAbstractTableModel

import numpy as np
from collections.abc import Iterable

from .electrode import Electrode

class CapModel(QAbstractTableModel):
    """CapModel class for displaying a list of electrodes in a Qt application."""
    def __init__(self, data: list = []):
        super().__init__()
        self._data = data
        self._labels = []
        
        # define Electrode class attributes to display in the table
        self._display_keys = ('label', 'modality')
        
    def set_labels(self, labels: list) -> None: 
        self._labels = labels

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._display_keys)
    
    def get_electrode(self, index: int) -> Electrode:
        return self._data[index]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole) -> str:
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                value = self._data[index.row()][self._display_keys[index.column()]]
                return str(value)
            
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return str(self._display_keys[section])
        return super().headerData(section, orientation, role)

    def insert_electrode(self, electrode: Electrode, parent=QModelIndex()) -> None:
        self.beginInsertRows(parent, self.rowCount(), self.rowCount())
        self._data.append(electrode)
        self.endInsertRows()
    
    def remove_electrode(self, electrode_index, parent=QModelIndex()) -> None:
        self.beginRemoveRows(parent, self.rowCount(), self.rowCount())
        self._data.pop(electrode_index)
        self.endRemoveRows()
    
    def _calculate_distances(self, target_coordinates: Iterable[float]) -> list[float]:
        """Calculates the distances between the given point and all points in the electrode cap."""
        distances = []
        for electrode in self._data:
            point = np.array(electrode.coordinates)
            distances.append(np.linalg.norm(point-target_coordinates))
        return distances    

    def remove_closest_electrode(self, target_coordinates: Iterable[float]) -> None:
        """Removes the point in the electrode cap closest to the given point."""
        distances = self._calculate_distances(target_coordinates)
        
        # remove the point with the smallest distance
        if len(distances) > 0:
            min_index= np.argmin(distances)
            # id_to_remove = self._data[min_index]['ID']
            self.remove_electrode(min_index)
    
    def get_next_id(self) -> str:
        """Returns the next available ID for a new point."""
        numeric_ids = [int(x['eID']) for x in self._data if x['eID'].isdigit()]
        if len(numeric_ids) == 0:
            return '0'
        else:    
            return str(np.max(numeric_ids) + 1)

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole:
            self._data[index.row()][self._display_keys[index.column()]] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable
