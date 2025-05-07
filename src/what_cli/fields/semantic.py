from dataclasses import dataclass, field
from datetime import datetime
from numbers import Number
from pathlib import Path
from urllib import parse as urlparse

import humanize
from psutil import Process

from .basic import Field


@dataclass(kw_only=True)
class EntityName(Field):
    """Represents the name of an entity"""

    name: str
    styles: str | list[str] = field(default_factory=lambda: "bold")

    @property
    def content(self) -> str:
        return self.name


@dataclass
class NumberField(Field):
    """Represents a number"""

    value: Number

    @property
    def content(self) -> str:
        """Format as string"""
        if isinstance(self.value, int):
            return f"{self.value:,}"
        elif isinstance(self.value, float):
            return f"{self.value:,.2f}"
        else:
            raise ValueError(f"Unsupported type: {type(self.value)}")


@dataclass(kw_only=True)
class QuotedField(Field):
    """Represents a field with quotes"""

    value: str
    styles: str | list[str] = field(default_factory=lambda: "italic")

    @property
    def content(self) -> str:
        return self.value


@dataclass
class PathUri(Field):
    path: Path

    @property
    def content(self) -> str:
        """Format as string"""
        encoded = urlparse.quote(str(self.path))
        return f"file://{encoded}"


@dataclass(kw_only=True)
class ProcessField(Field):
    process: Process

    def __post_init__(self):
        self.hint = f"PID: {self.process.pid}"

    @property
    def content(self) -> str:
        return self.process.name()


@dataclass
class MemorySize(Field):
    """Represents a memory size"""

    bytes: int

    @property
    def content(self) -> str:
        size_str = humanize.naturalsize(self.bytes)
        return size_str


@dataclass(kw_only=True)
class SystemUser(Field):
    """Represents a system user or group"""

    name: str

    styles: str | list[str] = field(default_factory=lambda: ["bold yellow"])

    @property
    def content(self) -> str:
        """Format as string"""
        return self.name


@dataclass
class Timestamp(Field):
    timestamp: datetime

    def __post_init__(self):
        self.hint = humanize.naturaltime(self.timestamp)

    @property
    def content(self):
        """Format as string"""
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class ImageDimensions(Field):
    """Represents image dimensions"""

    x: int
    y: int

    @property
    def content(self) -> str:
        """Format as string"""
        return f"{self.x} x {self.y}"
