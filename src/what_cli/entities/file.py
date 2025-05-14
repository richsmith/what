import grp
import os
import pwd
from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Self, override

import magic
from ascii_magic import AsciiArt
from PIL import Image
from pygments import lexers
from rich.console import Group, Text
from rich.panel import Panel
from rich.table import Table

from ..fields import (
    Code,
    DirectorySummary,
    EntityName,
    FilePermissions,
    ImageDimensions,
    LabelField,
    MemorySize,
    NumberField,
    PathUri,
    QuotedField,
    Section,
    SystemUser,
    Timestamp,
)
from .entity import Entity


@dataclass(kw_only=True)
class File(Entity):
    """Container for file information"""

    entity_type: str = "File"
    icon: str = "📄"
    path: Path

    @property
    def name(self) -> Path:
        """Return the file name"""
        return EntityName(name=self.path.name)

    @property
    def size(self) -> MemorySize:
        """Return the file size"""
        return MemorySize(bytes=self._stat.st_size)

    @property
    def mime_type(self) -> str:
        """Return the file mime type"""
        mime = magic.from_file(self.path, mime=True)
        return mime

    @property
    def _stat(self) -> os.stat_result:
        """Return the stat result for the file"""
        return self.path.lstat()

    @property
    def created(self) -> Timestamp:
        """Return the file creation time"""
        return Timestamp(datetime.fromtimestamp(self._stat.st_ctime))

    @property
    def modified(self) -> Timestamp:
        """Return the file modification time"""
        return Timestamp(datetime.fromtimestamp(self._stat.st_mtime))

    @property
    def accessed(self) -> Timestamp:
        """Return the file access time"""
        return Timestamp(datetime.fromtimestamp(self._stat.st_atime))

    @property
    def permissions(self) -> FilePermissions:
        return FilePermissions(self._stat.st_mode)

    @property
    def owner(self) -> SystemUser:
        """Return the file owner"""
        try:
            return SystemUser(name=pwd.getpwuid(self._stat.st_uid).pw_name)
        except KeyError:
            return SystemUser(name=str(self._stat.st_uid))

    @property
    def user_group(self) -> SystemUser:
        """Return the file group"""
        try:
            return SystemUser(name=grp.getgrgid(self._stat.st_gid).gr_name)
        except KeyError:
            return SystemUser(name=str(self._stat.st_gid))

    def get_sections(self) -> list[Section]:
        """Return sections for the file presentation"""

        yield self.get_basic()
        yield self.get_permissions()
        yield self.get_timestamps()

        yield from self.get_content_sections()

    def get_basic(self) -> list[Section]:
        basic = Section("File")
        basic.add(LabelField("Name", self.name))
        self.add_path_fields(basic)
        basic.add(LabelField("URI", PathUri(path=self.path)))
        basic.add(LabelField("Size", self.size))
        basic.add(LabelField("Type", QuotedField(value=self.entity_type)))
        return basic

    def get_permissions(self) -> list[Section]:
        ownership = Section("Permissions")
        ownership.add(LabelField("Owner", self.owner))
        ownership.add(LabelField("Group", self.user_group))
        ownership.add(LabelField("RWX", self.permissions))
        return ownership

    def get_timestamps(self) -> list[Section]:
        """Return sections for the file timestamps"""
        timestamps = Section("Timestamps")
        timestamps.add(LabelField("Created", self.created))
        timestamps.add(LabelField("Modified", self.modified))
        timestamps.add(LabelField("Accessed", self.accessed))
        return timestamps

    def get_content_sections(self) -> list[Section]:
        """Return sections for the file type-specific content"""
        return []

    def add_path_fields(self, section):
        section.add(LabelField("Path", self.path))

    @override
    @classmethod
    def match(cls, name: str) -> Self | None:
        """Match the file by its name"""
        abs_path = os.path.abspath(name)
        if os.path.isfile(abs_path) or os.path.isdir(abs_path):
            return FileFactory.from_path(abs_path)
        else:
            return None


@dataclass
class RegularFile(File, ABC):
    def get_basic(self) -> list[Section]:
        basic = super().get_basic()
        basic.add(LabelField("MIME", self.mime_type))
        return basic


@dataclass
class ImageFile(RegularFile):
    """Container for image file information"""

    @property
    def dimensions(self) -> ImageDimensions:
        """Return the image dimensions"""
        return ImageDimensions(*self.get_dimensions())

    def get_dimensions(self) -> tuple[int, int]:
        """Return the image dimensions"""
        with Image.open(self.path) as image:
            width, height = image.size
        return width, height

    def get_content_sections(self) -> list[Section]:
        """Return sections for the image file presentation"""
        image_info = Section("Image Information")
        image_info.add(LabelField("Dimensions", self.dimensions))
        yield image_info

    def get_preview(self, cols=40):
        art = AsciiArt.from_image(self.path)
        ascii_art = art.to_ascii(columns=cols)

        grid = Table.grid()
        [grid.add_column() for _ in range(cols)]
        for row in ascii_art.splitlines():
            row = Text.from_ansi(row)
            grid.add_row(*row)

        return Panel(
            grid,
            highlight=False,
            title="Preview",
            border_style="dim",
            title_align="center",
        )


class FileFactory:
    """Factory class for creating file objects"""

    @staticmethod
    def from_path(file_path: str) -> File:
        """Analyze a file and return a File object with all details"""
        path = Path(file_path)

        if path.is_symlink():
            file = SymlinkFile(path=path)
        elif path.is_dir():
            file = Directory(path=path)
        elif FileFactory.is_image_file(path):
            file = ImageFile(path=path)
        elif CodeFile.match(path=path):
            file = CodeFile(path=path)
        else:
            file = RegularFile(path=path)

        return file

    @staticmethod
    def is_image_file(file_path: str) -> bool:
        """Check if the file is an image file"""
        # FIXME testing
        return file_path.name.lower().endswith(
            (".png", ".jpg", ".jpeg", ".gif", ".webp")
        )


@dataclass
class TextFile(RegularFile, ABC):

    def __post_init__(self):
        from chardet.universaldetector import UniversalDetector

        detector = UniversalDetector()

        line_count = 0
        word_count = 0
        with open(self.path, "rb") as f:
            for line in f:
                line_count += 1
                word_count += len(line.split())
                if not detector.done:
                    detector.feed(line)
        detector.close()

        self._line_count = line_count
        self._word_count = word_count

        self._encoding = detector.result["encoding"]

    @property
    def line_count(self) -> int:
        """Return the number of lines in the text file"""
        return NumberField(self._line_count)

    @property
    def word_count(self) -> int:
        """Return the number of words in the text file"""
        return NumberField(self._word_count)

    @property
    def encoding(self) -> str:
        """Return the encoding of the text file"""
        return QuotedField(value=self._encoding)

    def get_content_sections(self) -> list[Section]:
        """Return sections for the text file presentation"""
        text_info = Section("Content Information")
        text_info.add(LabelField("Encoding", self.encoding))
        text_info.add(LabelField("Lines", self.line_count))
        text_info.add(LabelField("Words", self.word_count))
        yield text_info


@dataclass
class SymlinkFile(File):
    entity_type: str = "Symlink"
    icon: str = "🔗"

    @property
    def target(self) -> str:
        """Return the target of the symlink"""
        try:
            return os.readlink(self.path)
        except FileNotFoundError:
            return None

    def add_path_fields(self, section):
        super().add_path_fields(section)
        section.add(LabelField("Link", "↪️ " + self.target))


@dataclass
class Directory(File):
    entity_type: str = "Directory"
    icon: str = "📁"

    def __post_init__(self):
        self._items = list(self.path.iterdir())

    @property
    def summary(self) -> str:
        """Return a summary of the directory content"""
        files = sum(1 for item in self._items if item.is_file())
        directories = sum(1 for item in self._items if item.is_dir())
        return DirectorySummary(directories=directories, files=files)

    def get_content_sections(self) -> list[Section]:
        """Return sections for the directory content"""
        directory_info = Section("Directory Information")
        directory_info.add(LabelField("Contains", self.summary))
        yield directory_info


@dataclass
class CodeFile(TextFile):

    @classmethod
    def get_language(cls, path: Path) -> str:
        sample = path.read_text()[: (80 * 10)]
        lexer = lexers.guess_lexer(sample)
        if lexer:
            return lexer.name

    @classmethod
    def match(cls, path: Path):
        try:
            matched_a_language = bool(cls.get_language(path))
            return matched_a_language
        except Exception:
            return False

    @property
    def language(self) -> str:
        return self.get_language(self.path)

    def get_preview(self, max_lines=20):
        """Return the code content"""
        code = Code(self.path, max_lines=max_lines)
        preview_content = [code]
        if missing_lines := max(0, self._line_count - max_lines):
            preview_content.append(f"... +{missing_lines} lines")
        return Group(*preview_content)

    def get_content_sections(self) -> list[Section]:
        """Return sections for the code file presentation"""
        code_info = Section("Code Information")
        code_info.add(LabelField("Language", self.language))
        code_info.add(LabelField("Encoding", self.encoding))
        code_info.add(LabelField("Lines", self.line_count))
        yield code_info
