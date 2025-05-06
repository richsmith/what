import os
import pwd

from .entities import Entity, File, Process, User


def match(name) -> Entity:

    for entity_type in (File, Process, User):
        if entity := entity_type.match(name):
            return entity

    else:
        raise Exception(f"No match found for {name}")
