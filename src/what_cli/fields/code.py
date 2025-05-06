from dataclasses import dataclass
from pathlib import Path

from rich.console import Console, ConsoleOptions, RenderResult
from rich.padding import Padding
from rich.syntax import Syntax


@dataclass
class Code:
    path: Path

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Rich console representation for the code"""
        syntax = Syntax.from_path(
            self.path, line_numbers=True, code_width=79, line_range=(1, 20)
        )
        yield Padding(syntax, (1, 0, 0, 0))
