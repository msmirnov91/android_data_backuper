import argparse
import json
import logging
import os
from pathlib import Path
import shlex
import subprocess
import sys
from tqdm import tqdm


SOURCE_DIR_PREFIX = "/sdcard/"
LOG_FILE = os.path.join(".", "backup.log")


def get_logger():
    return logging.getLogger("ADBItemsBackup")


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
                    prog='Items backup',
                    description='Copies files from phone to HDD',
                    epilog='Good luck!')
    parser.add_argument('-l', '--list',
                    action='store_true')
    parser.add_argument('-cp', '--copy',
                    action='store_true')
    parser.add_argument("--log-level",
                    choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                    default="INFO")
    parser.add_argument("--config",
                    type=str,
                    default="./config.json")
    return parser.parse_args()


def parse_config(config_path):
    with open(config_path, "r") as f:
        return json.load(f)


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
    def wrapper(config):
        ensure_device_is_ready()
        source_dir_names = config["common"]["android_dirs"]
        dest_root_dir = config["common"]["local_dir"]
        for source_dir_name in source_dir_names:
            print(f"Processing directory {source_dir_name}...")
            source_dir = SOURCE_DIR_PREFIX + source_dir_name
            dest_dir = os.path.join(dest_root_dir, source_dir_name)
            func(source_dir, dest_dir)
    return wrapper


def list_items_internal(source_dir, dest_dir):
    get_logger().debug(f"Listing files from {source_dir}...")

    cmd_result = run_adb_command(["shell", "ls", source_dir])
    result = cmd_result.stdout.split("\n")
    return [r for r in result if r]


@adb_cmd
def list_items(source_dir, dest_dir):
    result = list_items_internal(source_dir, dest_dir)
    exts = set()
    for f in result:
        exts.add(f[-3:])

    result_str = '\n'.join(result)
    get_logger().debug(f"{result_str}\n,\n exts: {exts}")
    print(f"Items count: {len(result)}")
    return result


@adb_cmd
def pull_items(source_dir, dest_dir):
    get_logger().debug(f"Making dir {dest_dir}...")
    os.makedirs(dest_dir, exist_ok=True)

    get_logger().debug(f"Copying from {source_dir} to {dest_dir}")
    items = list_items_internal(source_dir, dest_dir)
    for i in tqdm(items, desc="Pulled", unit="item"):
        get_logger().debug(f"Processing file {i}")

        old_path = os.path.join(source_dir, i)
        new_path = os.path.join(dest_dir, i)

        if os.path.exists(new_path):
            get_logger().debug(f"File {i} exists, skipping")
            continue

        run_adb_command(["pull", old_path, new_path])
        run_adb_command(["shell", "rm", shlex.quote(old_path)])

    return None


def main():
    args = parse_args()
    config = parse_config(args.config)
    logger = setup_logger(args.log_level)

    if args.list:
        list_items(config)
    if args.copy:
        pull_items(config)


if __name__ == "__main__":
    main()
