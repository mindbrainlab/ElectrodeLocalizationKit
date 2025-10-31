from enum import Enum
from dataclasses import dataclass


@dataclass
class ElectrodeConfig:
    num_electrodes: int
    min_area: int
    min_distance: int
    min_radius: int
    max_radius: int
    n_segments: int


@dataclass
class MarkerConfig:
    num_green_markers: int
    min_area: int
    min_distance: int
    min_radius: int
    max_radius: int


class ViewType(Enum):
    """
    Possible 3D head scan view angles, with metadata about electrodes and markers.
    """

    FRONT = (
        "front",
        ElectrodeConfig(
            num_electrodes=None,
            min_area=500,
            min_distance=50,
            min_radius=15,
            max_radius=25,
            n_segments=750,
        ),
        MarkerConfig(
            num_green_markers=3,
            min_area=1500,
            min_distance=150,
            min_radius=20,
            max_radius=35,
        ),  # 2 - 1
    )
    BACK = (
        "back",
        ElectrodeConfig(
            num_electrodes=None,
            min_area=500,
            min_distance=50,
            min_radius=10,
            max_radius=25,
            n_segments=750,
        ),
        MarkerConfig(
            num_green_markers=0,
            min_area=1500,
            min_distance=75,
            min_radius=20,
            max_radius=35,
        ),  # 0
    )
    TOP = (
        "top",
        ElectrodeConfig(
            num_electrodes=None,
            min_area=500,
            min_distance=50,
            min_radius=15,
            max_radius=25,
            n_segments=750,
        ),
        MarkerConfig(
            num_green_markers=0,
            min_area=1500,
            min_distance=150,
            min_radius=20,
            max_radius=35,
        ),  # 0
    )
    RIGHT = (
        "right",
        ElectrodeConfig(
            num_electrodes=None,
            min_area=500,
            min_distance=75,
            min_radius=15,
            max_radius=25,
            n_segments=750,
        ),
        MarkerConfig(
            num_green_markers=8,
            min_area=1500,
            min_distance=100,
            min_radius=20,
            max_radius=35,
        ),  # 3 - 2 - 3
    )
    LEFT = (
        "left",
        ElectrodeConfig(
            num_electrodes=None,
            min_area=500,
            min_distance=75,
            min_radius=15,
            max_radius=25,
            n_segments=750,
        ),
        MarkerConfig(
            num_green_markers=8,
            min_area=1500,
            min_distance=100,
            min_radius=20,
            max_radius=35,
        ),  # 3 - 2 - 3
    )
    FRONT_TOP = (
        "front_top",
        ElectrodeConfig(
            num_electrodes=None,
            min_area=500,
            min_distance=50,
            min_radius=10,
            max_radius=25,
            n_segments=750,
        ),
        MarkerConfig(
            num_green_markers=7,
            min_area=1500,
            min_distance=150,
            min_radius=15,
            max_radius=35,
        ),  # 2 - 3 - (2)
    )
    BACK_TOP = (
        "back_top",
        ElectrodeConfig(
            num_electrodes=None,
            min_area=500,
            min_distance=50,
            min_radius=10,
            max_radius=25,
            n_segments=750,
        ),
        MarkerConfig(
            num_green_markers=7,
            min_area=1500,
            min_distance=75,
            min_radius=20,
            max_radius=35,
        ),  # 3 - 1 - 2 - 1
    )
    FRONT_RIGHT = (
        "front_right",
        ElectrodeConfig(
            num_electrodes=None,
            min_area=500,
            min_distance=75,
            min_radius=15,
            max_radius=25,
            n_segments=750,
        ),
        MarkerConfig(
            num_green_markers=0,
            min_area=1500,
            min_distance=100,
            min_radius=20,
            max_radius=35,
        ),  # 0
    )
    FRONT_LEFT = (
        "front_left",
        ElectrodeConfig(
            num_electrodes=None,
            min_area=500,
            min_distance=75,
            min_radius=15,
            max_radius=25,
            n_segments=750,
        ),
        MarkerConfig(
            num_green_markers=0,
            min_area=1500,
            min_distance=100,
            min_radius=20,
            max_radius=35,
        ),  # 0
    )
    BACK_RIGHT = (
        "back_right",
        ElectrodeConfig(
            num_electrodes=None,
            min_area=500,
            min_distance=75,
            min_radius=15,
            max_radius=25,
            n_segments=750,
        ),
        MarkerConfig(
            num_green_markers=0,
            min_area=1500,
            min_distance=100,
            min_radius=20,
            max_radius=35,
        ),  # 0
    )
    BACK_LEFT = (
        "back_left",
        ElectrodeConfig(
            num_electrodes=None,
            min_area=500,
            min_distance=75,
            min_radius=15,
            max_radius=25,
            n_segments=750,
        ),
        MarkerConfig(
            num_green_markers=0,
            min_area=1500,
            min_distance=100,
            min_radius=20,
            max_radius=35,
        ),  # 0
    )
    TOP_RIGHT = (
        "top_right",
        ElectrodeConfig(
            num_electrodes=None,
            min_area=500,
            min_distance=75,
            min_radius=15,
            max_radius=25,
            n_segments=750,
        ),
        MarkerConfig(
            num_green_markers=0,
            min_area=1500,
            min_distance=100,
            min_radius=20,
            max_radius=35,
        ),  # 0
    )
    TOP_LEFT = (
        "top_left",
        ElectrodeConfig(
            num_electrodes=None,
            min_area=500,
            min_distance=75,
            min_radius=15,
            max_radius=25,
            n_segments=750,
        ),
        MarkerConfig(
            num_green_markers=0,
            min_area=1500,
            min_distance=100,
            min_radius=20,
            max_radius=35,
        ),  # 0
    )

    # Not needed views
    BOTTOM = ("bottom", None, None)
    FRONT_BOTTOM = ("front_bottom", None, None)
    BACK_BOTTOM = ("back_bottom", None, None)
    BOTTOM_RIGHT = ("bottom_right", None, None)
    BOTTOM_LEFT = ("bottom_left", None, None)

    def __init__(self, label: str, electrode_cfg: ElectrodeConfig, marker_cfg: MarkerConfig):
        self.label = label
        self.electrode_cfg = electrode_cfg
        self.marker_cfg = marker_cfg

    def __str__(self) -> str:
        return (
            f"{self.label} "
            f"(electrodes={self.electrode_cfg.num_electrodes if self.electrode_cfg else 'NA'}, "
            f"min_area_e={self.electrode_cfg.min_area if self.electrode_cfg else 'NA'}, "
            f"min_dist_e={self.electrode_cfg.min_distance if self.electrode_cfg else 'NA'}, "
            f"markers={self.marker_cfg.num_green_markers if self.marker_cfg else 'NA'}, "
            f"min_area_m={self.marker_cfg.min_area if self.marker_cfg else 'NA'}, "
            f"min_dist_m={self.marker_cfg.min_distance if self.marker_cfg else 'NA'}, "
            f"radius=[{self.marker_cfg.min_radius}, {self.marker_cfg.max_radius}]"
        )
