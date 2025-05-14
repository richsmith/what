from dataclasses import dataclass, field
from typing import Any

from rich.console import Console, ConsoleOptions, RenderResult
from rich.table import Table


@dataclass
class LabelField:
    """Represents a name-value pair in a section"""

    name: str
    value: Any

    def __str__(self) -> str:
        return f"{self.name}: {self.value}"


@dataclass
class Section:
    """Represents a section of related fields"""

    name: str
    fields: list[LabelField] = field(default_factory=list)
    show_header: bool = False

    def add(self, field: LabelField) -> None:
        """Add a field to the section"""
        self.fields.append(field)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Rich console representation for the section"""

        table_options = {
            "show_header": self.show_header,
            "box": None,
            "expand": False,
        }

        if self.show_header:
            table_options["title"] = self.name
            table_options["title_justify"] = "left"
            table_options["title_style"] = "bold"

        table = Table(**table_options)
        table.add_column(justify="right", highlight=False)
        table.add_column(justify="left", highlight=True)
        for section_field in self.fields:
            name = section_field.name
            value = section_field.value
            if not hasattr(value, "__rich_console__"):
                value = str(value)
            table.add_row(name, value)
        yield table
