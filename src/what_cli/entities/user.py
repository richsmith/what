import grp
import pwd
import spwd
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import psutil

from ..fields import EntityName, Field, FileSize, Section, SystemUser, Timestamp
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

        # Get shadow information if possible (requires root)
        try:
            self.shadow = spwd.getspnam(self.username)
            self.has_shadow = True
        except (KeyError, PermissionError):
            self.has_shadow = False

        # cache here to avoid multiple calls to psutil
        self.processes = [
            p.pid
            for p in psutil.process_iter(["pid", "username"])
            if p.info["username"] == self.username
        ]
        # Also cache
        self.users = psutil.users()

    @property
    def name(self) -> str:
        """Return the user's name"""
        # Try to get full name from GECOS field
        gecos = self.pwd_entry.pw_gecos.split(",")
        full_name = gecos[0] if gecos and gecos[0] else self.username

        return EntityName(full_name)

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
    def secondary_groups(self) -> List[str]:
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
    def last_password_change(self) -> Optional[Timestamp]:
        """Return the date of the last password change"""
        if not self.has_shadow:
            return None

        if self.shadow.sp_lstchg > 0:
            change_date = datetime.fromtimestamp(self.shadow.sp_lstchg * 86400)
            return Timestamp(change_date)

        return None

    @property
    def password_expires(self) -> Optional[Timestamp]:
        """Return the date when the password expires"""
        if not self.has_shadow:
            return None

        if self.shadow.sp_lstchg > 0 and self.shadow.sp_max > 0:
            expire_date = datetime.fromtimestamp(
                (self.shadow.sp_lstchg + self.shadow.sp_max) * 86400
            )
            return Timestamp(expire_date)

        return None

    @property
    def account_expires(self) -> Optional[Timestamp]:
        """Return the date when the account expires"""
        if not self.has_shadow:
            return None

        if self.shadow.sp_expire > 0:
            expire_date = datetime.fromtimestamp(self.shadow.sp_expire * 86400)
            return Timestamp(expire_date)

        return None

    @property
    def account_locked(self) -> bool:
        """Return True if the account is locked"""
        if not self.has_shadow:
            return None

        # Common ways to lock an account in shadow password
        return self.shadow.sp_pwd.startswith(("!", "*")) and len(self.shadow.sp_pwd) > 1

    @property
    def is_logged_in(self) -> bool:
        """Return True if the user is currently logged in"""
        return any(u.name == self.username for u in self.users)

    @property
    def login_sessions(self) -> List[dict]:
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
    def memory_usage(self) -> FileSize:
        """Return the total memory used by this user's processes"""
        total_memory = 0
        for pid in self.processes:
            try:
                process = psutil.Process(pid)
                total_memory += process.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return FileSize(total_memory)

    def get_sections(self) -> list[Section]:
        """Return sections for the user presentation"""

        # Basic user information
        basic = Section("User Information")
        basic.add(Field("Name", self.name))
        basic.add(Field("Username", SystemUser(self.username)))
        basic.add(Field("UID", self.uid))
        basic.add(
            Field("Type", "System User" if self.is_system_user else "Regular User")
        )

        # Group membership
        groups = Section("Group Membership")
        groups.add(Field("Primary Group", f"{self.primary_group} ({self.gid})"))
        if self.secondary_groups:
            groups.add(Field("Secondary Groups", ", ".join(self.secondary_groups)))

        # Account details
        account = Section("Account Details")
        account.add(Field("Home", self.home_directory))
        account.add(Field("Shell", self.shell))

        if self.has_shadow:
            account.add(
                Field("Last Password Change", self.last_password_change or "Never")
            )
            if self.password_expires:
                account.add(Field("Password Expires", self.password_expires))
            if self.account_expires:
                account.add(Field("Account Expires", self.account_expires))
            account.add(
                Field("Account Status", "Locked" if self.account_locked else "Active")
            )

        # Login status
        login = Section("Login Status")
        login.add(Field("Logged In", True if self.is_logged_in else False))

        if self.is_logged_in:
            for i, session in enumerate(self.login_sessions, 1):
                login.add(Field(f"Session {i}", f"Terminal: {session['terminal']}"))
                if session["host"]:
                    login.add(Field(f"From Host {i}", session["host"]))
                login.add(Field(f"Login Time {i}", session["started"]))

        # Process information
        processes = Section("Processes")
        processes.add(Field("Process Count", self.process_count))
        processes.add(Field("Memory Usage", self.memory_usage))

        return [basic, groups, account, login, processes]
