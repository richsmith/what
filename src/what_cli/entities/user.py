import grp
import pwd
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Self, override

import psutil

from ..fields import EntityName, LabelField, MemorySize, Section, SystemUser, Timestamp
from .entity import Entity


@dataclass(kw_only=True)
class User(Entity):
    """Container for user information"""

    entity_type: str = "User"
    icon: str = "👤"
    username: str

    def __post_init__(self):
        """Initialize the user information"""
        try:
            self.pwd_entry = pwd.getpwnam(self.username)
        except KeyError:
            self.errors.append(f"User '{self.username}' not found")
            return

        # cache here to avoid multiple calls to psutil
        self.processes = [
            p.pid
            for p in psutil.process_iter(["pid", "username"])
            if p.info["username"] == self.username
        ]
        # Also cache
        self.users = psutil.users()

    @override
    @classmethod
    def match(cls, name: str) -> Self | None:
        try:
            pwd.getpwnam(name)
            return User(username=name)
        except KeyError:
            return False

    @property
    def name(self) -> str:
        """Return the user's name"""
        # Try to get full name from GECOS field
        gecos = self.pwd_entry.pw_gecos.split(",")
        full_name = gecos[0] if gecos and gecos[0] else self.username

        return EntityName(name=full_name)

    @property
    def uid(self) -> int:
        """Return the user ID"""
        return self.pwd_entry.pw_uid

    @property
    def gid(self) -> int:
        """Return the primary group ID"""
        return self.pwd_entry.pw_gid

    @property
    def primary_group(self) -> str:
        """Return the primary group name"""
        try:
            return grp.getgrgid(self.pwd_entry.pw_gid).gr_name
        except KeyError:
            return str(self.pwd_entry.pw_gid)

    @property
    def secondary_groups(self) -> list[str]:
        """Return list of secondary groups"""
        groups = []
        for group in grp.getgrall():
            if self.username in group.gr_mem and group.gr_name != self.primary_group:
                groups.append(group.gr_name)

        return groups

    @property
    def home_directory(self) -> Path:
        """Return the home directory"""
        return Path(self.pwd_entry.pw_dir)

    @property
    def shell(self) -> str:
        """Return the login shell"""
        return self.pwd_entry.pw_shell

    @property
    def is_system_user(self) -> bool:
        """Return True if this is a system user"""
        # Common threshold for system users on Linux
        return self.uid < 1000

    @property
    def is_logged_in(self) -> bool:
        """Return True if the user is currently logged in"""
        return any(u.name == self.username for u in self.users)

    @property
    def login_sessions(self) -> list[dict]:
        """Return information about current login sessions"""
        sessions = []
        for session in self.users:
            if session.name == self.username:
                sessions.append(
                    {
                        "terminal": session.terminal,
                        "host": session.host if hasattr(session, "host") else None,
                        "started": Timestamp(datetime.fromtimestamp(session.started)),
                    }
                )

        return sessions

    @property
    def process_count(self) -> int:
        """Return the number of processes owned by this user"""
        return len(self.processes)

    @property
    def memory_usage(self) -> MemorySize:
        """Return the total memory used by this user's processes"""
        total_memory = 0
        for pid in self.processes:
            try:
                process = psutil.Process(pid)
                total_memory += process.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return MemorySize(bytes=total_memory)

    def get_sections(self) -> list[Section]:
        """Return sections for the user presentation"""

        # Basic user information
        basic = Section("User Information")
        basic.add(LabelField("Name", self.name))
        basic.add(LabelField("Username", SystemUser(name=self.username)))
        basic.add(LabelField("UID", self.uid))
        basic.add(
            LabelField("Type", "System User" if self.is_system_user else "Regular User")
        )

        # Group membership
        groups = Section("Group Membership")
        groups.add(LabelField("Primary Group", f"{self.primary_group} ({self.gid})"))
        if self.secondary_groups:
            groups.add(LabelField("Secondary Groups", ", ".join(self.secondary_groups)))

        # Account details
        account = Section("Account Details")
        account.add(LabelField("Home", self.home_directory))
        account.add(LabelField("Shell", self.shell))

        # Login status
        login = Section("Login Status")
        login.add(LabelField("Logged In", True if self.is_logged_in else False))

        if self.is_logged_in:
            for i, session in enumerate(self.login_sessions, 1):
                login.add(
                    LabelField(f"Session {i}", f"Terminal: {session['terminal']}")
                )
                if session["host"]:
                    login.add(LabelField(f"From Host {i}", session["host"]))
                login.add(LabelField(f"Login Time {i}", session["started"]))

        # Process information
        processes = Section("Processes")
        processes.add(LabelField("Process Count", self.process_count))
        processes.add(LabelField("Memory Usage", self.memory_usage))

        return [basic, groups, account, login, processes]
