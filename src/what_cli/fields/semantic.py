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
    is_percentage: bool = False

    @property
    def content(self) -> str:
        suffix = "%" if self.is_percentage else ""

        if isinstance(self.value, int):
            return f"{self.value:,}{suffix}"
        elif isinstance(self.value, float):
            return f"{self.value:,.2f}{suffix}"
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


@dataclass(kw_only=True)
class PathUri(Field):
    path: Path
    styles: str | list[str] = field(default_factory=lambda: "link")

    @property
    def content(self) -> str:
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
        return self.timestamp.strftime("%Y-%m-%d %H:%M:%S")


@dataclass
class DurationField(Field):
    """Represents a time duration"""

    seconds: int

    @property
    def content(self) -> str:
        return humanize.naturaldelta(self.seconds)


@dataclass
class Resolution(Field):
    """Represents image/video resolution"""

    x: int
    y: int

    @property
    def content(self) -> str:
        return f"{self.x} x {self.y}"


@dataclass
class Bitrate(Field):
    """Represents a bitrate value"""

    bps: int

    @property
    def content(self) -> str:
        return humanize.naturalsize(self.bps, binary=True, format="%.2f") + "/s"


@dataclass
class SampleRate(Field):
    """Represents a sample rate value"""

    hertz: int

    @property
    def content(self) -> str:
        return f"{self.hertz:,} Hz"


@dataclass
class FrameRate(Field):
    """Represents a frame rate value"""

    fps: float

    @property
    def content(self) -> str:
        return f"{self.fps:.2f} fps"


@dataclass
class DirectorySummary(Field):
    directories: int
    files: int

    def __post_init__(self):
        parts = []
        if self.directories:
            parts.append(f"{self.directories:,} directories")
        if self.files:
            parts.append(f"{self.files:,} files")
        self.hint = "; ".join(parts)

    @property
    def content(self) -> str:
        total = self.directories + self.files
        return f"{total:,} items"
