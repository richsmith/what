from ABC import ABC, abstractmethod


@dataclass
class Field:
    def hint(self) -> optional[str]:
        return None
