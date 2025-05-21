#!/usr/bin/env python3
"""
Add a timestamp to the version in a Python file.

Usage:
  python add_version_timestamp.py <file_path>

The script will locate the __version__ variable in the file and add
a .devYYYYMMDDHHMMSS timestamp suffix to it.
"""

import argparse
import datetime
import re
import sys


def add_timestamp_to_version(file_path):
    """
    Add a timestamp to the __version__ variable in the specified file.

    Args:
        file_path: Path to the Python file containing __version__

    Returns:
        0 on success, 1 on error
    """
    try:
        # Read the file
        with open(file_path, "r") as f:
            content = f.read()

        # Find the version string
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
        if not match:
            print(f"Error: Couldn't find __version__ in {file_path}")
            return 1

        current_version = match.group(1)

        # Remove existing dev suffix if present
        if ".dev" in current_version:
            base_version = current_version.split(".dev")[0]
        else:
            base_version = current_version

        # Add timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        new_version = f"{base_version}.dev{timestamp}"

        # Update the file
        new_content = re.sub(
            r'__version__\s*=\s*["\']([^"\']+)["\']',
            f'__version__ = "{new_version}"',
            content,
        )

        with open(file_path, "w") as f:
            f.write(new_content)

        print(f"Updated version: {current_version} → {new_version}")
        return 0

    except Exception as e:
        print(f"Error: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Add a timestamp to the __version__ variable in a Python file"
    )
    parser.add_argument(
        "file_path", help="Path to the Python file containing __version__"
    )

    args = parser.parse_args()

    return add_timestamp_to_version(args.file_path)


if __name__ == "__main__":
    sys.exit(main())
