import argparse
import logging
import os
from pathlib import Path
import shlex
import subprocess
import sys
from tqdm import tqdm


DEFAULT_SOURCE_DIR = "/sdcard/DCIM/Camera"
DEST_DIR = os.path.join("/", "media", "mikhail", "ADATA HD650", "auto_backup", "FromPhoneADB")

LOG_FILE = os.path.join(".", "backup.log")


def get_logger():
    return logging.getLogger("ADBPhotoBackup")


def setup_logger(level="INFO"):
    logger = get_logger()
    logger.setLevel(logging.DEBUG)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File (always DEBUG)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def parse_args():
    parser = argparse.ArgumentParser(
                    prog='Photos backup',
                    description='Copies photos and videos from phone to HDD',
                    epilog='Good luck!')
    parser.add_argument('-l', '--list',
                    action='store_true')
    parser.add_argument('-cp', '--copy',
                    action='store_true')
    parser.add_argument("--log-level",
                    choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                    default="INFO")
    return parser.parse_args()


def run_adb_command(cmd):
    try:
        get_logger().debug(f"Running cmd: adb {' '.join(cmd)}")

        result = subprocess.run(
            ["adb"] + cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result and result.returncode == 0:
            return result
        
        get_logger().debug("An error occured:")
        get_logger().debug(result.stderr if result else "Unknown error")
        get_logger().debug(f"Return code: {result.returncode}")
        exit(-1)
    except subprocess.TimeoutExpired:
        get_logger().debug("ADB: timeout")
        return None


def check_device():
    result = run_adb_command(["devices"])
    if result and "device" in result.stdout and "List of devices" in result.stdout:
        lines = result.stdout.strip().split('\n')
        for line in lines[1:]:
            if line.strip() and not line.startswith('*') and "device" in line:
                return True
    return False


def ensure_device_is_ready():
    if not check_device():
        get_logger().debug("Device is not plugged or not authorized.")
        get_logger().debug("Run the following command in terminal: adb devices")
        exit(-1)


def adb_cmd(func):
    def wrapper():
        ensure_device_is_ready()
        return func()
    return wrapper


@adb_cmd
def list_photos():
    get_logger().debug(f"Listing files from {DEFAULT_SOURCE_DIR}...")

    cmd_result = run_adb_command(["shell", "ls", DEFAULT_SOURCE_DIR])
    result = cmd_result.stdout.split("\n")
    result = [r for r in result if r]
    exts = set()
    for f in result:
        exts.add(f[-3:])

    result_str = '\n'.join(result)
    get_logger().debug(f"{result_str}\n cnt: {len(result)},\n exts: {exts}")
    return result


@adb_cmd
def pull_photos():
    get_logger().debug(f"Making dir {DEST_DIR}...")
    os.makedirs(DEST_DIR, exist_ok=True)

    get_logger().debug(f"Copying from {DEFAULT_SOURCE_DIR} to {DEST_DIR}")
    photos = list_photos()
    for p in tqdm(photos, desc="Pulled", unit="photo"):
        get_logger().debug(f"Processing file {p}")

        old_path = os.path.join(DEFAULT_SOURCE_DIR, p)
        new_path = os.path.join(DEST_DIR, p)

        if os.path.exists(new_path):
            get_logger().debug(f"File {p} exists, skipping")
            continue

        run_adb_command(["pull", old_path, new_path])
        run_adb_command(["shell", "rm", shlex.quote(old_path)])

    return None


def main():
    args = parse_args()
    logger = setup_logger(args.log_level)

    if args.list:
        list_photos()
    if args.copy:
        pull_photos()


if __name__ == "__main__":
    main()
