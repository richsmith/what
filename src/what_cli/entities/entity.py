from abc import ABC
from dataclasses import dataclass

from rich.console import Console, ConsoleOptions, RenderResult, group
from rich.padding import Padding
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

        content = self.get_content()

        MIN_CONTENT_WIDTH = 60
        MIN_PREVIEW_WIDTH = 40
        console_width = options.max_width
        show_console = console_width > MIN_CONTENT_WIDTH + MIN_PREVIEW_WIDTH

        preview = self.get_preview()
        if preview is None or show_console is False:
            main = content
        else:
            main = Table(show_header=False, box=None, padding=0, expand=True)
            main.add_column("Content", min_width=MIN_CONTENT_WIDTH)
            main.add_column("Preview", min_width=MIN_PREVIEW_WIDTH)
            padded_preview = Padding(preview, (1, 0, 0, 0))
            main.add_row(content, padded_preview)

        yield Panel(
            main,
            title=self.get_title(),
            title_align="left",
            padding=(0, 1, 1, 1),
        )

    def match(self, query: str) -> bool:
        """Return True if this entity matches the given query string."""
        raise NotImplementedError("Entities must provide matching functionality")
