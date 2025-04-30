#!/usr/bin/env python3
import argparse
import sys

from .entities.file import FileFactory
from .formatter import Formatter

"""
what - A human-friendly file properties viewer for the command line
"""


def what(file_path, no_headers=False):
    """Main function to analyze and display file information"""
    try:
        entity = FileFactory.from_path(file_path)
        Formatter.format(entity)
        return 0

    except Exception as exception:
        print(f"Error: {str(exception)}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Display file properties in a human-friendly way"
    )
    parser.add_argument("file", nargs="+", help="Path to the file(s) to examine")
    parser.add_argument(
        "--no-headers",
        action="store_true",
        help="Display fields without section headers",
    )
    parser.add_argument("-v", "--version", action="version", version="what 1.0.0")

    args = parser.parse_args()

    exit_code = 0
    for file_path in args.file:
        if len(args.file) > 1:
            # Add spacing between multiple files
            if file_path != args.file[0]:
                print("\n")

        result = what(file_path, args.no_headers)
        if result != 0:
            exit_code = result

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
