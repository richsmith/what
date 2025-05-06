from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import psutil
from psutil import Process as ProcessObj

from ..fields import Field, FileSize, Section, SystemUser, Timestamp
from .entity import Entity


@dataclass(kw_only=True)
class Process(Entity):
    """Container for computer process information"""

    entity_type: str = "Process"
    icon: str = "⚙️ "
    process: ProcessObj
    _children: List["Process"] = field(default_factory=list, repr=False)
    _parent: Optional["Process"] = field(default=None, repr=False)

    def __post_init__(self):
        """Post-initialization to set up the process object"""
        # super().__post_init__()
        self.update_children()

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

    # New properties for parent-child relationships
    @property
    def parent_pid(self) -> Optional[int]:
        """Return the parent process ID"""
        try:
            return self.process.ppid()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return None

    @property
    def parent(self) -> Optional["Process"]:
        """Return the parent Process object"""
        return self._parent

    @parent.setter
    def parent(self, parent_process: "Process"):
        """Set the parent Process object"""
        self._parent = parent_process

    @property
    def children(self) -> List["Process"]:
        """Return child processes"""
        return self._children

    def update_children(self):
        """Update children list from psutil"""
        try:
            child_processes = self.process.children()
            self._children = [Process(process=child) for child in child_processes]
            # Set parent reference in children
            for child in self._children:
                child.parent = self
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self._children = []

    # Additional process information
    @property
    def thread_count(self) -> int:
        """Return number of threads"""
        try:
            return len(self.process.threads())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0

    @property
    def io_stats(self) -> Dict[str, int]:
        """Return I/O statistics"""
        try:
            io = self.process.io_counters()
            return {
                "read_bytes": io.read_bytes,
                "write_bytes": io.write_bytes,
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {
                "read_bytes": 0,
                "write_bytes": 0,
            }

    def get_sections(self) -> list[Section]:
        """Return sections for the process presentation"""
        basic = Section("Process Information")
        basic.add(Field("Name", self.name))
        basic.add(Field("PID", self.pid))
        basic.add(Field("Status", self.status))
        basic.add(Field("Thread Count", self.thread_count))

        resources = Section("Resources")
        resources.add(Field("CPU", f"{self.cpu}%"))
        resources.add(Field("Nice", self.nice))
        resources.add(Field("Memory", self.memory))
        resources.add(Field("Memory %", f"{self.memory_percent:.2f}%"))

        io = Section("I/O Statistics")
        io_stats = self.io_stats
        io.add(Field("Read", FileSize(io_stats["read_bytes"])))
        io.add(Field("Write", FileSize(io_stats["write_bytes"])))

        started = Section("Started")
        started.add(Field("Started", self.started))
        started.add(Field("Command", self.command))
        started.add(Field("User", self.user))

        return [basic, resources, io, started]
