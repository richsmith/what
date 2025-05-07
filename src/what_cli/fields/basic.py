from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from rich.console import Console, ConsoleOptions, RenderResult


@dataclass(kw_only=True)
class Field(ABC):
    hint: str | None = None
    styles: str | list[str] = field(default_factory=list)
    hint_styles: str | list[str] = field(default_factory=lambda: ["italic"])

    @property
    @abstractmethod
    def content(self) -> str:
        raise NotImplementedError("Subclasses must provide content")

    def _with_style(self, obj, styles):
        style_str = " ".join(styles) if isinstance(styles, list) else styles
        return f"[{style_str}]{obj}[/]" if style_str else obj

    def assemble_field(self):

        text = self._with_style(self.content, self.styles)

        if self.hint:
            hint_str = self._with_style(self.hint, self.hint_styles)
            text += f" ({hint_str})"

        return text

    def __str__(self) -> str:
        return str(self.assemble_field())

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        text = self.assemble_field()
        yield text
