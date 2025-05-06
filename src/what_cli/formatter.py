from rich.console import Console

console = Console()


class Formatter:
    """Responsible for formatting file information for display"""

    @staticmethod
    def format(data):
        console.print(data)
