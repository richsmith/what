import argparse
import sys
import traceback

from . import __version__, matcher
from .entities.file import FileFactory
from .formatter import Formatter


def handle_args():
    parser = argparse.ArgumentParser(
        description="Display file properties in a human-friendly way"
    )
    parser.add_argument("name", nargs="+", help="Name of entity to describe")
    parser.add_argument(
        "--headers", action="store_true", help="Display section headers"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Display debug information"
    )
    parser.add_argument("-v", "--version", action="version", version=__version__)

    return parser.parse_args()


def run():
    """Match entity and display a summary"""
    try:
        args = handle_args()
        name = args.name[0]

        entity = matcher.match(name)
        Formatter.format(entity)

        return 0

    except Exception as exception:
        Formatter.format("[red]" + str(exception) + "[/]")
        if args.debug:
            traceback.print_exc()
        return 1
