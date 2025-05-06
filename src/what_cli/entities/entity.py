from dataclasses import dataclass

from rich.console import Console, ConsoleOptions, Group, RenderResult, group
from rich.panel import Panel

from ..fields import Section


@dataclass(kw_only=True)
class Entity:
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

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Rich console representation of the entity"""
        yield Panel(
            self.get_content(),
            title=self.get_title(),
            title_align="left",
        )
