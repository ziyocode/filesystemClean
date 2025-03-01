import os
import sys
import time
import logging
import gzip
import shutil
from datetime import datetime
from typing import Generator, Tuple

# Configuration File Path
CONFIG_FILE: str = "./filesystem_clean.conf"

# Logging Configuration
LOGDIR: str = "/tmp/filesystem_clean"
LOG_EXPIRED_DAYS: int = 10
LOG_DATE: str = datetime.today().strftime("%Y%m%d")
LOG_FILENAME: str = os.path.join(LOGDIR, f"filesystem_clean_{LOG_DATE}.log")

def setup_logger() -> logging.Logger:
    """Setup and return the logger."""
    os.makedirs(LOGDIR, exist_ok=True)
    logger = logging.getLogger("filesystem_clean")
    logger.setLevel(logging.INFO)

    # Console and File Handlers
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(LOG_FILENAME)

    formatter = logging.Formatter(
        fmt="%(asctime)s %(name)s [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Initialize Logger
logger = setup_logger()

# Current Time
current_time: float = time.time()

def read_config_file(file_path: str) -> Generator[Tuple[str, str], None, None]:
    """Read and parse the configuration file."""
    if not os.path.exists(file_path):
        logger.error(f"Configuration file not found: {file_path}")
        sys.exit("Configuration file is missing.")

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            # Skip comments and empty lines
            if line.startswith("#") or not line.strip():
                continue
            yield tuple(line.strip().split(":"))


def validate_config(line):
    """Validate a single line of the configuration."""
    if len(line) != 6:
        raise ValueError("Invalid configuration format. Expected 6 fields.")

    mode, work_dir, scope, condition, target_date, method = line
    if mode not in {"RUN", "DEBUG"}:
        raise ValueError(f"Invalid mode: {mode}. Expected 'RUN' or 'DEBUG'.")

    if not os.path.isdir(work_dir):
        raise ValueError(f"Invalid directory: {work_dir}")

    if scope not in {"ALL", "SPECIFIC"}:
        raise ValueError(f"Invalid scope: {scope}. Expected 'ALL' or 'SPECIFIC'.")

    if not target_date.isdigit() or int(target_date) <= 0:
        raise ValueError(
            f"Invalid target_date: {target_date}. Must be a positive integer."
        )

    if method not in {"DELETE", "NULL", "GZIP"}:
        raise ValueError(
            f"Invalid method: {method}. Expected 'DELETE', 'NULL', or 'GZIP'."
        )

    return mode, work_dir, scope, condition, int(target_date), method


def process_file(mode, method, file_path):
    """Apply the specified method to the file."""
    try:
        if method == "DELETE":
            if mode == "RUN":
                os.remove(file_path)
                logger.info(f"[RUN] Deleted file: {file_path}")
            else:
                logger.info(f"[DEBUG] Would delete file: {file_path}")

        elif method == "NULL" and os.path.getsize(file_path) > 0:
            if mode == "RUN":
                with open(file_path, "w", encoding="utf-8"):
                    pass
                logger.info(f"[RUN] Nullified file: {file_path}")
            else:
                logger.info(f"[DEBUG] Would nullify file: {file_path}")

        elif method == "GZIP" and not file_path.endswith(".gz"):
            if mode == "RUN":
                gzip_path = f"{file_path}.gz"
                with open(file_path, "rb") as f_in, gzip.open(gzip_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
                os.remove(file_path)
                logger.info(f"[RUN] Gzipped file: {file_path}")
            else:
                logger.info(f"[DEBUG] Would gzip file: {file_path}")
    except Exception as e:
        logger.error(f"Failed to process file {file_path}: {e}")


def process_directory(mode, work_dir, scope, condition, target_time, method):
    """Walk through the directory and process files based on the configuration."""
    for root, _, files in os.walk(work_dir):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_age = current_time - os.path.getmtime(file_path)

            if file_age > target_time:
                if scope == "ALL" or (
                    scope == "SPECIFIC" and file_name.startswith(condition)
                ):
                    process_file(mode, method, file_path)


def clean_empty_directories(mode, work_dir):
    """Remove empty directories."""
    for root, dirs, files in os.walk(work_dir, topdown=False):
        if not dirs and not files:
            if mode == "RUN":
                os.rmdir(root)
                logger.info(f"[RUN] Deleted empty directory: {root}")
            else:
                logger.info(f"[DEBUG] Would delete empty directory: {root}")


def clean_old_logs(log_dir, expired_days):
    """Remove old log files."""
    for root, _, files in os.walk(log_dir):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_age = current_time - os.path.getmtime(file_path)

            if file_age > expired_days * 24 * 3600:
                os.remove(file_path)
                logger.info(f"Deleted old log file: {file_path}")


if __name__ == "__main__":
    logger.info("Starting filesystem_clean.py...")

    try:
        for config_line in read_config_file(CONFIG_FILE):
            try:
                mode, work_dir, scope, condition, target_date, method = validate_config(
                    config_line
                )
                target_time = target_date * 24 * 3600

                logger.info(f"Processing configuration: {config_line}")
                logger.debug(f"Mode: {mode}")
                logger.debug(f"Directory: {work_dir}")
                logger.debug(f"Scope: {scope}")
                logger.debug(f"Condition: {condition}")
                logger.debug(f"Target Date: {target_date}")
                logger.debug(f"Method: {method}")

                process_directory(mode, work_dir, scope, condition, target_time, method)
                clean_empty_directories(mode, work_dir)
            except ValueError as e:
                logger.error(f"Configuration error: {e}")

        # Clean old logs
        clean_old_logs(LOGDIR, LOG_EXPIRED_DAYS)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

    logger.info("filesystem_clean.py completed successfully.")
