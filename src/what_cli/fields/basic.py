from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(kw_only=True)
class Field:

    hint: str | None = None

    @property
    def content(self) -> str:
        raise NotImplementedError("Subclasses must provide content")

    def __str__(self) -> str:
        """Format as string"""
        content = self.content
        if self.hint:
            hint = Hint(self.hint)
            content += f" ({hint})"
        return content


@dataclass
class Hint(Field):
    """Represent(Field)s a hint for the field"""

    hint: str | None = None

    def __str__(self) -> str:
        return f"[italic]{self.hint}[/]" if self.hint else ""
