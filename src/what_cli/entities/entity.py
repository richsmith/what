from abc import ABC
from dataclasses import dataclass

from rich.console import Console, ConsoleOptions, RenderResult, group
from rich.panel import Panel
from rich.table import Table

from ..fields import Section


@dataclass(kw_only=True)
class Entity(ABC):
    """Base class for all things"""

    entity_type: str = "Unknown"
    error: bool = False
    errors: list[str] = None

    def get_title(self):
        return f"{self.icon} {self.entity_type}: {self.name}"

    def get_sections(self) -> list[Section]:
        yield []

    @group(fit=True)
    def get_content(self) -> list[Section]:
        yield from self.get_sections()

    def get_preview(self) -> RenderResult:
        """Override this method to provide a preview renderable for the entity.
        Return None if no preview is available."""
        return None

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Rich console representation of the entity"""
        print(f"{options.max_width=}")
        content = self.get_content()

        preview = self.get_preview()
        if preview is None:
            main = content
        else:
            main = Table(show_header=False, box=None, padding=0, expand=True)
            main.add_column("Content", min_width=79)
            main.add_column("Preview", max_width=79)
            main.add_row(content, preview)

        yield Panel(
            main,
            title=self.get_title(),
            title_align="left",
        )

    def match(self, query: str) -> bool:
        """Return True if this entity matches the given query string."""
        raise NotImplementedError("Entities must provide matching functionality")
