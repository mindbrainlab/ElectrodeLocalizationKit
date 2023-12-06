from .electrode import Electrode
from .head_models import HeadScan
from .cap_model import CapModel


class Session:
    def __init__(self, session_id: str, head_scan: HeadScan, electrode_cap: CapModel):
        self.session_id = session_id
        self.head_scan = head_scan
        self.electrode_cap = electrode_cap
        