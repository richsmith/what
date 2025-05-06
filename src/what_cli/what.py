import argparse
import traceback
from typing import Any

from rich.console import Console

from . import DESCRIPTION, matcher

console = Console()


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
    parser.add_argument("-v", "--version", action="version", version=DESCRIPTION)

    return parser.parse_args()


def display(data: Any) -> None:
    # entities are responsible for their own display
    console.print(data)


def run():
    """Match entity and display a summary"""
    try:
        args = handle_args()
        name = args.name[0]

        entity = matcher.match(name)
        display(entity)

        return 0

    except Exception as exception:
        Formatter.format("[red]" + str(exception) + "[/]")
        if args.debug:
            traceback.print_exc()
        return 1
