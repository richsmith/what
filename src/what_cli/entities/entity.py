from abc import ABC
from argparse import ArgumentParser
from dataclasses import dataclass

from rich.console import Console, ConsoleOptions, RenderResult, group
from rich.panel import Panel
from rich.table import Table

from ..fields import Section
from .preview import Preview

MIN_CONTENT_WIDTH = 60
MIN_PREVIEW_WIDTH = 40


@dataclass(kw_only=True)
class Entity(ABC):
    """Base class for all things"""

    args: ArgumentParser = None
    entity_type: str = "Unknown"
    error: bool = False
    errors: list[str] = None

    def get_title(self):
        return f"{self.icon} {self.entity_type}: {self.name}"

    def get_sections(self) -> list[Section]:
        yield []

    @group(fit=True)
    def get_content(self) -> list[Section]:
        from rich.padding import Padding

        for i, section in enumerate(self.get_sections()):
            if i > 0:
                yield Padding("")
            yield section

    def get_preview(self, max_height) -> RenderResult:
        """
        Override this method to provide a preview renderable for
        the entity. Return None if no preview is available.
        """
        return None

    @classmethod
    def provides_preview(cls) -> bool:
        # A bit hacky :P
        # This reports whether the subclass has an implemented get_preview
        if cls.get_preview != Entity.get_preview:
            return True

    def _measure_height(self, renderable, console: Console) -> int:
        capture_console = Console()
        line_count = 1
        for segment in capture_console.render(renderable, capture_console.options):
            if segment.text:
                line_count += segment.text.count("\n")
        return line_count

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Rich console representation of the entity"""
        content = self.get_content()

        console_width = options.max_width
        room_for_preview = console_width > MIN_CONTENT_WIDTH + MIN_PREVIEW_WIDTH
        preview_on = not self.args.no_preview
        preview_available = preview_on and room_for_preview and self.provides_preview()

        if preview_available:
            main = Table(show_header=False, box=None, padding=0, expand=True)
            main.add_column("Content")
            main.add_column("Preview", min_width=MIN_PREVIEW_WIDTH)
            content_height = self._measure_height(content, console)
            preview = Preview(self.get_preview(content_height), content_height)
            main.add_row(content, preview)
        else:
            main = content

        yield Panel(
            main,
            title=self.get_title(),
            title_align="left",
            padding=(1, 1, 1, 1),
        )

    def match(self, query: str) -> bool:
        """Return True if this entity matches the given query string."""
        raise NotImplementedError("Entities must provide matching functionality")
