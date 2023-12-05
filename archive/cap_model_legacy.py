
class CapModel_render(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self._plotter = None
        self._labels = []
        
        # define Electrode class attributes to display in the table
        self._display_keys = ('label', 'modality')

    def set_plotter(self, plotter: vd.Plotter) -> None:
        self._plotter = plotter
        
    def set_labels(self, labels: list) -> None: 
        self._labels = labels

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._display_keys)

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
            point = np.array([electrode['x'], electrode['y'], electrode['z']])
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
        numeric_ids = [int(x) for x in self._data if x['ID'].isdigit()]
        if len(numeric_ids) == 0:
            return '0'
        else:    
            return str(np.max(numeric_ids) + 1)
    
    def render(self) -> None:
        if self._plotter is None:
            raise ValueError('Plotter not set')
        
        points_unlabeled = []
        points_labeled = []
        for row in self._data.iterrows():
            if row[1]['label'] in self._labels:
                points_labeled.append([row[1]['x'], row[1]['y'], row[1]['z']])
            else:
                points_unlabeled.append([row[1]['x'], row[1]['y'], row[1]['z']])
        
        if len(self._plotter.actors) > 2:
            self._plotter.remove(self._plotter.actors[2:])
        
        if len(points_unlabeled) > 0:
            spheres = vd.Spheres(points_unlabeled, r=0.004, res=8, c='r5', alpha=1)
            self._plotter.add(spheres)
        
        if len(points_labeled) > 0:
            spheres = vd.Spheres(points_labeled, r=0.004, res=8, c='b5', alpha=1)
            self._plotter.add(spheres)
            
        self._plotter.render()
            
        self.layoutChanged.emit()

    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole:
            self._data[index.row()][self._display_keys[index.column()]] = value
            # self.render()
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable


# Pandas cap model
class CapModelPd(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data
        self._plotter = None
        self._labels = []

    def set_plotter(self, plotter: vd.Plotter) -> None:
        self._plotter = plotter
        
    def set_labels(self, labels: list) -> None: 
        self._labels = labels

    def rowCount(self, parent=QModelIndex()):
        return self._data.shape[0]

    def columnCount(self, parent=QModelIndex()):
        return self._data.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole) -> str:
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
                value = self._data.iloc[index.row(), index.column()]
                return str(value)

    def insert_electrode(self, row: Electrode, parent=QModelIndex()) -> None:
        self.beginInsertRows(parent, self.rowCount(), self.rowCount())
        self._data = pd.concat([self._data, row])
        self.endInsertRows()
    
    def remove_electrode(self, id, parent=QModelIndex()) -> None:
        self.beginRemoveRows(parent, self.rowCount(), self.rowCount())
        self._data = self._data[self._data.ID != id]
        self.endRemoveRows()
    
    def remove_closest_electrode(self, electrode_to_remove: Electrode) -> None:
        """Removes the point in the electrode cap closest to the given point."""
        point_to_remove = np.array([electrode_to_remove.x, electrode_to_remove.y, electrode_to_remove.z])
        distances = []
        for point in self._data[['x', 'y', 'z']].values:
            distances.append(np.linalg.norm(point-point_to_remove))
        
        # remove the point with the smallest distance
        if len(distances) > 0:
            min_idx = np.argmin(distances)
            id_to_remove = self._data.iloc[min_idx]['ID']
            self.remove_electrode(id_to_remove)
    
    def get_next_id(self) -> str:
        """Returns the next available ID for a new point."""
        numeric_ids = [int(x) for x in self._data.ID.to_list() if x.isdigit()]
        if len(numeric_ids) == 0:
            return '0'
        else:    
            return str(np.max(numeric_ids) + 1)
    
    def render(self) -> None:
        if self._plotter is None:
            raise ValueError('Plotter not set')
        
        points_unlabeled = []
        points_labeled = []
        for row in self._data.iterrows():
            if row[1]['label'] in self._labels:
                points_labeled.append([row[1]['x'], row[1]['y'], row[1]['z']])
            else:
                points_unlabeled.append([row[1]['x'], row[1]['y'], row[1]['z']])
        
        if len(self._plotter.actors) > 2:
            self._plotter.remove(self._plotter.actors[2:])
        
        if len(points_unlabeled) > 0:
            spheres = vd.Spheres(points_unlabeled, r=0.004, res=8, c='r5', alpha=1)
            self._plotter.add(spheres)
        
        if len(points_labeled) > 0:
            spheres = vd.Spheres(points_labeled, r=0.004, res=8, c='b5', alpha=1)
            self._plotter.add(spheres)
            
        self._plotter.render()
            
        self.layoutChanged.emit()