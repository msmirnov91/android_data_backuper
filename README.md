# Android data backuper

Currently tested only on Ubuntu. Needs pre-created config file. Before usage, activate the developer mode on the phone, run `adb devices` in terminal and allow debugging via USB.

# Config

```json
{
    "common": {
        "android_dirs": [
            "dir1",
            "dir2"
        ],
        "local_dir": "/path/to/local/dir"
    }
}
```

# How to run

Supposed to run from the repo root dir.

CMD args:

- `-l`, `--list`: just list the files from phone dirs
- `-cp`, `--copy`: copy files from dirs and delete them on the phone
- `--log-level`: logging level, one of "DEBUG", "INFO", "WARNING", "ERROR"

Run command example:
```bash
python3 backup.py -cp
```

# How to debug

To ensure everything works try to list the files:
```bash
python3 backup.py -l
```

To enable CMD logs output specify debigging level `DEBUG`:
```bash
python3 backup.py -cp --log-level DEBUG
```

Moreover, the debug logs always availabie in the file `backup.log`, which is created during the backup process.

Example of the `adb devices` command output:
```bash
user@comp-name:~$ adb devices
* daemon not running; starting now at tcp:<PORT> # starting daemon
* daemon started successfully
List of devices attached
R4CFB1RY6GO     unauthorized  # Device is plugged but not ready,
# allow USB debugging by following instructions on the phone's screen

# USB debugging was allowed, repeating command
user@comp-name:~$ adb devices
List of devices attached
R4CFB1RY6GO     device  # Now device is ready for backuping data
```

# Known problems

On a large folders adb commands can fail with timeout. Therefore the files are copied one-by-one.
