import os
from typing import Optional

import psutil

from .entities.entity import Entity
from .entities.file import FileFactory
from .entities.process import Process


def is_int(name: str) -> bool:
    try:
        int(name)
        return True
    except ValueError:
        return False


def match(name) -> Optional[Entity]:

    # check if name parses to an int

    # if name resolves to a file then return a file
    if os.path.isfile(name):
        return FileFactory.from_path(name)
    # if name resolves to a process ID then return a process
    elif is_int(name) and psutil.pid_exists(int(name)):
        pid = int(name)
        p = psutil.Process(pid)
        return Process(process=p)
    # if name resolves to a process name then return the process
    elif psutil.process_iter():
        for p in psutil.process_iter(attrs=["pid", "name"]):
            if p.info["name"] == name:
                return Process(process=p)

    else:
        raise Exception(f"No match found for {name}")
