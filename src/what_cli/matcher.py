import os
import pwd
from typing import Optional

import psutil

from .entities.entity import Entity
from .entities.file import FileFactory
from .entities.process import Process
from .entities.user import User


def is_int(name: str) -> bool:
    try:
        int(name)
        return True
    except ValueError:
        return False


def user_exists(username: str) -> bool:
    """Check if a user exists on the system"""
    try:
        pwd.getpwnam(username)
        return True
    except KeyError:
        return False


def find_process_by_pid(name: str) -> Optional[Process]:
    if is_int(name) and psutil.pid_exists(int(name)):
        pid = int(name)
        process = psutil.Process(pid)
        return process


def find_process_by_name(name: str) -> Optional[Process]:
    """Find a process by its name"""
    for process in psutil.process_iter(attrs=["pid", "name"]):
        if process.info["name"] == name:
            return process


def match_process(name: str) -> Optional[Process]:
    """Match a process by its name or PID"""
    if is_int(name):
        return find_process_by_pid(name)
    elif process := find_process_by_name(name):
        return process
    else:
        return None


def match_file(name: str) -> Optional[FileFactory]:
    """Match a file by its name"""
    abs_path = os.path.abspath(name)
    if os.path.isfile(abs_path) or os.path.isdir(abs_path):
        return FileFactory.from_path(abs_path)
    else:
        return None


def match(name) -> Optional[Entity]:
    # check if name parses to an int
    # if name resolves to a file then return a file
    if path := match_file(name):
        return path

    # if name resolves to a process then return the process
    elif process := match_process(name):
        return Process(process=process)

    # if name resolves to a username then return the user
    elif user_exists(name):
        return User(username=name)

    else:
        raise Exception(f"No match found for {name}")
