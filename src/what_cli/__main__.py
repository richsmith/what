#!/usr/bin/env python3
from . import what


def main():
    try:
        what.run()
    except Exception as exception:
        print(f"Error: {str(exception)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
