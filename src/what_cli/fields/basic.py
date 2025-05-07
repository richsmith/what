from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from rich.console import Console, ConsoleOptions, RenderResult
from rich.text import Text


@dataclass(kw_only=True)
class Field(ABC):
    hint: str | None = None
    styles: str | list[str] = field(default_factory=list)
    hint_styles: str | list[str] = field(default_factory=lambda: ["italic"])

    @property
    @abstractmethod
    def content(self) -> str:
        raise NotImplementedError("Subclasses must provide content")

    def __str__(self) -> str:
        return str(self.assemble_field())

    def _as_tuple(self, text, styles):
        style_str = " ".join(styles)
        return (text, style_str) if style_str else text

    def assemble_field(self):
        parts = []
        content_tuple = self._as_tuple(str(self.content), self.styles)
        parts.append(content_tuple)

        if self.hint:
            hint_tuple = self._as_tuple(f" ({self.hint})", self.hint_styles)
            parts.append(hint_tuple)

        text = Text.assemble(*parts)
        return text

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        text = self.assemble_field()
        yield text


@dataclass
class Hint:
    hint: str | None = None

    def __str__(self) -> str:
        return f"[italic]{self.hint}[/]" if self.hint else ""
