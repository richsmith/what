from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib import parse as urlparse

import humanize

from .basic import Field


@dataclass
class EntityName:
    """Represents the name of an entity"""

    name: str

    def __str__(self) -> str:
        return f"[bold]{self.name}[/bold]"


@dataclass
class PathUri:
    path: Path

    def __str__(self) -> str:
        """Format as string"""
        encoded = urlparse.quote(str(self.path))
        return f"file://{encoded}"


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


@dataclass
class ImageDimensions:
    """Represents image dimensions"""

    x: int
    y: int

    def __str__(self) -> str:
        """Format as string"""
        return f"{self.x} x {self.y}"
