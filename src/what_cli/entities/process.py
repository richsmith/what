from dataclasses import dataclass
from datetime import datetime
from typing import Self, override

import psutil
from psutil import Process as ProcessObj
from rich.tree import Tree

from ..fields import (
    LabelField,
    MemorySize,
    ProcessField,
    Section,
    SystemUser,
    Timestamp,
)
from .entity import Entity


@dataclass(kw_only=True)
class Process(Entity):
    """Container for computer process information"""

    entity_type: str = "Process"
    icon: str = "⚙️ "
    process: ProcessObj

    @override
    @classmethod
    def match(cls, name: str) -> Self | None:
        def is_int(name: str) -> bool:
            try:
                int(name)
                return True
            except ValueError:
                return False

        def find_process_by_pid(name: str) -> Process | None:
            if is_int(name) and psutil.pid_exists(int(name)):
                pid = int(name)
                process = psutil.Process(pid)
                return process

        def find_process_by_name(name: str) -> Process | None:
            for process in psutil.process_iter(attrs=["pid", "name"]):
                if process.info["name"] == name:
                    return process

        if process := (find_process_by_pid(name) or find_process_by_name(name)):
            return cls(process=process)

    @property
    def name(self) -> str:
        """Return the process name"""
        return f"[bold]{self.process.name()}[/]"

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
    def memory(self) -> MemorySize:
        """Return the process memory usage"""
        percent = self.process.memory_percent()
        percent_str = f"{percent:.2f}%"
        return MemorySize(bytes=self.process.memory_info().rss, hint=percent_str)

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
        return SystemUser(name=self.process.username())

    @property
    def thread_count(self) -> int:
        """Return number of threads"""
        try:
            return len(self.process.threads())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0

    @property
    def io_stats(self) -> dict[str, int]:
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
        basic.add(LabelField("Name", self.name))
        basic.add(LabelField("PID", self.pid))
        basic.add(LabelField("Status", self.status))
        basic.add(LabelField("Threads", self.thread_count))

        resources = Section("Resources")
        resources.add(LabelField("CPU", f"{self.cpu}%"))
        resources.add(LabelField("Nice", self.nice))
        resources.add(LabelField("Memory", self.memory))

        io = Section("I/O Statistics")
        io_stats = self.io_stats
        io.add(LabelField("Read", MemorySize(io_stats["read_bytes"])))
        io.add(LabelField("Write", MemorySize(io_stats["write_bytes"])))

        started = Section("Started")
        started.add(LabelField("Started", self.started))
        started.add(LabelField("Command", self.command))
        started.add(LabelField("User", self.user))

        return [basic, resources, io, started]

    def get_lineage(self) -> list[ProcessObj]:
        """Return a list of ancestor processes"""
        ancestors = [self.process]
        current = ancestors[0]
        while current.ppid() != 0:
            try:
                parent = psutil.Process(current.ppid())
                ancestors.append(parent)
                current = parent
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
        return list(reversed(ancestors))

    def get_children(self) -> list[ProcessObj]:
        """Return a list of child processes"""
        children = []
        try:
            for child in self.process.children(recursive=False):
                children.append(child)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return children

    def get_preview(self) -> Tree:
        """Return a tree view of process relationships (ancestors and children)"""

        ANCESTOR = ["blue"]
        THIS = ["bold", "yellow"]
        CHILD = ["green"]

        def create_tree_node(process, styles):
            """Create a tree node with process information"""
            if process is self.process:
                styles = THIS
            return ProcessField(process=process, styles=styles)

        try:
            lineage = self.get_lineage()
            process_tree = Tree(create_tree_node(lineage[0], ANCESTOR))

            node = process_tree
            for ancestor in lineage[1:]:
                node = node.add(
                    create_tree_node(ancestor, ANCESTOR),
                )

            for child in self.get_children():
                node.add(create_tree_node(child, CHILD))

            return process_tree

        except Exception as e:
            error_tree = Tree("[bold red]Error generating process tree[/]")
            error_tree.add(f"[red]{str(e)}[/]")
            return error_tree
