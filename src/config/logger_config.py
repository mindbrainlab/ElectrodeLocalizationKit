import datetime
import logging
import sys

from pathlib import Path


def setup_logger(level: int = logging.INFO) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    file_root_path = Path("logs")
    file_root_path.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists
    timestamp = datetime.datetime.now().strftime("%d_%B_%Y-%H%M")
    log_filename = f"{timestamp}.log"
    file_handler = logging.FileHandler(file_root_path / log_filename)
    file_handler.setLevel(level)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    if not root_logger.hasHandlers():
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

    for noisy_logger in []:
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
