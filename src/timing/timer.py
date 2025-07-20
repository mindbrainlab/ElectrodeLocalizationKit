import time
import csv
from pathlib import Path


class StageTimer:
    def __init__(self):
        self.stages = []

    def start(self):
        self._start_time = time.perf_counter()

    def log(self, stage_name: str):
        end_time = time.perf_counter()
        elapsed = end_time - self._start_time
        self.stages.append((stage_name, elapsed))
        self._start_time = end_time

    def save(self, subject_id: str, filepath: Path):
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Subject", "Stage", "ElapsedSeconds"])
            for stage, duration in self.stages:
                writer.writerow([subject_id, stage, f"{duration:.6f}"])
