from dataclasses import dataclass
from datetime import datetime

from psutil import Process as ProcessObj

from ..fields import FileSize, SystemUser, Timestamp
from ..presentation import Field, Section
from .entity import Entity


@dataclass(kw_only=True)
class Process(Entity):
    """Container for computer process information"""

    entity_type: str = "Process"
    icon: str = "⚙️ "

    process: ProcessObj

    @property
    def name(self) -> str:
        """Return the process name"""
        return f"[bold]{self.process.name()}[/bold]"

    @property
    def pid(self) -> int:
        """Return the process ID"""
        return self.process.pid

    @property
    def status(self) -> str:
        """Return the process status"""
        return self.process.status()

    @property
    def started(self) -> str:
        """Return the process start time"""
        return Timestamp(datetime.fromtimestamp(self.process.create_time()))

    @property
    def memory(self) -> FileSize:
        """Return the process memory usage"""
        return FileSize(self.process.memory_info().rss)

    @property
    def nice(self) -> int:
        """Return the process nice value"""
        return self.process.nice()

    @property
    def cpu(self) -> float:
        """Return the process CPU usage"""
        return self.process.cpu_percent(interval=1)

    @property
    def command(self) -> str:
        """Return the process command line"""
        return " ".join(self.process.cmdline())

    @property
    def user(self) -> str:
        """Return the process username"""
        return SystemUser(self.process.username())

    def get_sections(self) -> list[Section]:
        """Return sections for the process presentation"""
        basic = Section("Process Information")
        basic.add(Field("Name", self.name))
        basic.add(Field("PID", self.pid))
        basic.add(Field("Status", self.status))

        resources = Section("Resources")
        resources.add(Field("CPU", f"{self.cpu}%"))
        resources.add(Field("Nice", self.nice))
        resources.add(Field("Memory", self.memory))

        started = Section("Started")
        started.add(Field("Started", self.started))
        started.add(Field("Command", self.command))
        started.add(Field("User", self.user))

        return [basic, resources, started]
