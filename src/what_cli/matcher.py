from .entities import Entity, File, Process, User


def match(name, candidate_entities=None) -> Entity:

    if candidate_entities is None:
        # Match entities in the order in which we expect to be most
        # commonly used
        candidate_entities = [File, Process, User]

    for entity_type in candidate_entities:
        if entity := entity_type.match(name):
            return entity

    else:
        raise Exception(f"No match found for {name}")
