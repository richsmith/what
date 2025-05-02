import stat
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

import humanize


@dataclass
class EntityName:
    """Represents the name of an entity"""

    name: str

    def __str__(self) -> str:
        return f"[bold]{self.name}[/bold]"


@dataclass
class FileSize:
    """Represents a file size"""

    bytes: int

    def __str__(self) -> str:
        size_str = humanize.naturalsize(self.bytes)
        if "Bytes" not in size_str:
            bytes = self.bytes
            size_str += f" ({bytes:,} Byte{'s'[:bytes ^ 1]})"
        return size_str

    def human_readable(self) -> str:
        return


class Permission(Enum):
    """File permission bits"""

    READ = "r"
    WRITE = "w"
    EXECUTE = "x"

    def __str__(self) -> str:
        return self.value

    @property
    def colour(self) -> str:
        """Return the color associated with the permission"""
        if self == Permission.READ:
            return "yellow"
        elif self == Permission.WRITE:
            return "red"
        elif self == Permission.EXECUTE:
            return "green"
        else:
            return "white"


class PermissionType(Enum):
    """Types of file permissions"""

    USER = "u"
    GROUP = "g"
    OTHER = "o"

    def __str__(self) -> str:
        return self.value


@dataclass
class FilePermission:
    """Represents a file permission bit"""

    permission: Permission
    permission_type: PermissionType
    value: bool

    NOT_SET: str = "-"

    def __str__(self) -> str:
        return self.__rich__()

    def __bool__(self) -> bool:
        return self.value

    def __rich__(self) -> str:
        """Rich representation for the permission bit"""
        if self:
            return f"[{self.permission.colour}]{self.permission.value}[/]"
        else:
            return self.NOT_SET


PERMISSION_TO_MASK: dict[tuple[Permission, PermissionType], int] = {
    (Permission.READ, PermissionType.USER): stat.S_IRUSR,
    (Permission.WRITE, PermissionType.USER): stat.S_IWUSR,
    (Permission.EXECUTE, PermissionType.USER): stat.S_IXUSR,
    (Permission.READ, PermissionType.GROUP): stat.S_IRGRP,
    (Permission.WRITE, PermissionType.GROUP): stat.S_IWGRP,
    (Permission.EXECUTE, PermissionType.GROUP): stat.S_IXGRP,
    (Permission.READ, PermissionType.OTHER): stat.S_IROTH,
    (Permission.WRITE, PermissionType.OTHER): stat.S_IWOTH,
    (Permission.EXECUTE, PermissionType.OTHER): stat.S_IXOTH,
}


@dataclass
class FilePermissions:
    """Represents file permissions"""

    mode: int

    def __str__(self) -> str:
        bits = self.get_bits()
        return "".join(list(map(lambda b: b.__str__(), bits)))

    def get_bits(self) -> list[FilePermission]:
        bits = []
        for permission_type in PermissionType:
            for permission in Permission:
                mask = PERMISSION_TO_MASK[(permission, permission_type)]
                bit = self.mode & mask
                permission_bit = FilePermission(permission, permission_type, bool(bit))
                bits.append(permission_bit)

        return bits


@dataclass
class SystemUser:
    """Represents a system user or group"""

    name: str
    id: int = None

    def __str__(self) -> str:
        """Format as string"""
        name = f"[bold yellow]{self.name}[/]"
        if self.id:
            name += f" (ID: {self.id})"
        return name


@dataclass
class Timestamp:
    timestamp: datetime

    def __str__(self):
        """Format as string"""
        iso = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        human = humanize.naturaltime(self.timestamp)
        return f"{iso} ([italic]{human}[/])"
