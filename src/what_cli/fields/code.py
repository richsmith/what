from dataclasses import dataclass
from pathlib import Path

from rich.console import Console, ConsoleOptions, RenderResult
from rich.padding import Padding
from rich.syntax import Syntax


@dataclass
class Code:
    path: Path
    max_lines: int = 20
    line_numbers: bool = True

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Rich console representation for the code"""
        syntax = Syntax.from_path(
            self.path,
            line_numbers=self.line_numbers,
            line_range=(1, self.max_lines),
        )
        yield Padding(syntax, (1, 1, 1, 0))
