import time
import csv
from pathlib import Path

import logging

logger = logging.getLogger(__name__)


class StageTimer:
    def __init__(self):
        logger.info("Stage timer initiated")
        self.stages = []

    def start(self):
        logger.info("Stage timer started")
        self._start_time = time.perf_counter()

    def log(self, stage_name: str):
        logger.info("Stage timer logged")
        end_time = time.perf_counter()
        elapsed = end_time - self._start_time
        self.stages.append((stage_name, elapsed))
        self._start_time = end_time

    def save(self, filepath: Path):
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Session", "Stage", "ElapsedSeconds"])
            for stage, duration in self.stages:
                writer.writerow([filepath.stem.split("_")[0], stage, f"{duration:.6f}"])
        logger.info("Stage timer log saved")


stage_timer = StageTimer()
stage_timer.start()
