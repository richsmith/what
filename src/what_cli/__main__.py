#!/usr/bin/env python3
import sys

from . import what


def main():
    try:
        return what.run()
    except Exception as exception:
        print(f"Error: {str(exception)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
