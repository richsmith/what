from rich.console import Console, ConsoleOptions, RenderResult
from rich.segment import Segment
from rich.style import Style
from rich.table import Table
from rich.text import Text


class Preview:
    """
    A wrapper that displays preview content. Enforces a maximum
    height by truncating if necessary.
    """

    def __init__(self, renderable, max_height: int):
        self.renderable = renderable
        self.max_height = max_height

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Render the preview, truncating to max_height while preserving formatting"""
        # Create a capture console to render the preview
        capture_console = Console(
            width=options.max_width,
            height=None,
            force_terminal=True,
            color_system=console.color_system,
            legacy_windows=console.legacy_windows,
            _environ={},
        )

        # Render the content to segments
        segments = list(capture_console.render(self.renderable, options))

        # Group segments by line
        lines = []
        current_line = []

        for segment in segments:
            if segment.text and "\n" in segment.text:
                parts = segment.text.split("\n")
                # Add the first part to current line
                if parts[0]:
                    current_line.append(
                        Segment(parts[0], segment.style, segment.control)
                    )

                # Handle middle parts
                for i in range(1, len(parts) - 1):
                    lines.append(current_line)
                    current_line = []
                    if parts[i]:
                        current_line.append(
                            Segment(parts[i], segment.style, segment.control)
                        )

                # Start new line with last part
                lines.append(current_line)
                current_line = []
                if parts[-1]:
                    current_line.append(
                        Segment(parts[-1], segment.style, segment.control)
                    )
            else:
                current_line.append(segment)

        # Don't forget the last line
        if current_line:
            lines.append(current_line)

        # Truncate to max_height
        if len(lines) > self.max_height:
            # Take exactly max_height lines (indicator will replace the last one)
            truncated_lines = lines[: self.max_height - 1]

            # Calculate remaining lines
            remaining_lines = len(lines) - len(truncated_lines)

            # Create the line count indicator with styling
            label_str = f"+{remaining_lines} lines"
            label = Text(label_str, style=Style(dim=True))
            indicator = Table(show_header=False, box=None, padding=0, expand=True)
            indicator.add_column(justify="left", highlight=False)
            indicator.add_column(justify="right", highlight=False)
            ellipsis = Text("...", style=Style(dim=True))
            indicator.add_row(ellipsis, label)

            # Replace the last line with the indicator
            truncated_lines[-1] = indicator

            # Yield all segments from truncated lines
            for i, line in enumerate(truncated_lines):
                if isinstance(line, list):
                    for segment in line:
                        yield segment
                else:  # Single segment
                    yield line

                if i < len(truncated_lines) - 1:  # Add newline except for last line
                    yield Segment("\n")
        else:
            # Yield all segments as is
            for i, line in enumerate(lines):
                for segment in line:
                    yield segment
                if i < len(lines) - 1:  # Add newline except for last line
                    yield Segment("\n")
