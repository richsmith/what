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
from mutagen import File as MutagenFile
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis
from PIL import Image
from pygments import lexers
from pymediainfo import MediaInfo
from rich.console import Group, Text
from rich.panel import Panel
from rich.table import Table

from ..fields import (
    Bitrate,
    Code,
    DirectorySummary,
    DurationField,
    EntityName,
    FilePermissions,
    FrameRate,
    LabelField,
    MemorySize,
    NumberField,
    PathUri,
    QuotedField,
    Resolution,
    SampleRate,
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
    def directory(self) -> Path:
        """Return the file directory"""
        if self.path.is_dir():
            return self.path
        else:
            return self.path.parent

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
        basic.add(LabelField("URI", PathUri(path=self.directory)))
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
    def resolution(self) -> Resolution:
        """Return the image resolution"""
        return Resolution(*self.get_resolution())

    def get_resolution(self) -> tuple[int, int]:
        """Return the image dimensions"""
        with Image.open(self.path) as image:
            width, height = image.size
        return width, height

    @override
    def get_content_sections(self) -> list[Section]:
        """Return sections for the image file presentation"""
        image_info = Section("Image Information")
        image_info.add(LabelField("Resolution", self.resolution))
        yield image_info

    @override
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


@dataclass
class AudioFile(RegularFile):
    """Container for audio file information"""

    def __post_init__(self):
        self._audio = MutagenFile(self.path)

    @property
    def duration(self) -> str:
        """Return the audio duration"""
        return DurationField(self._audio.info.length)

    @property
    def bitrate(self) -> str:
        if bitrate := getattr(self._audio.info, "bitrate", None):
            return Bitrate(bitrate)
        else:
            return None

    @property
    def sample_rate(self) -> str:
        if sample := getattr(self._audio.info, "sample_rate", None):
            return SampleRate(sample)
        else:
            return None

    @property
    def audio_type(self) -> str:
        if isinstance(self._audio, MP3):
            format_name = "MP3"
        elif isinstance(self._audio, FLAC):
            format_name = "FLAC"
        elif isinstance(self._audio, MP4):
            format_name = "MP4/M4A"
        elif isinstance(self._audio, OggVorbis):
            format_name = "Ogg Vorbis"
        else:
            format_name = self._audio.mime[0] if self._audio.mime else "Unknown"
        return QuotedField(value=format_name)

    @override
    def get_content_sections(self) -> list[Section]:
        audio_info = Section("Audio Information")
        audio_info.add(LabelField("Audio Format", self.audio_type))
        audio_info.add(LabelField("Duration", self.duration))
        if bitrate := self.bitrate:
            audio_info.add(LabelField("Bitrate", bitrate))
        if sample_rate := self.sample_rate:
            audio_info.add(LabelField("Sample Rate", sample_rate))
        yield audio_info


@dataclass
class VideoFile(RegularFile):
    """Container for video file information"""

    def __post_init__(self):
        self._media_info = MediaInfo.parse(str(self.path))
        self._video_track = None
        self._audio_track = None

        for track in self._media_info.tracks:
            if track.track_type == "Video" and not self._video_track:
                self._video_track = track
            elif track.track_type == "Audio" and not self._audio_track:
                self._audio_track = track

    @property
    def duration(self) -> str:
        if self._video_track and self._video_track.duration:
            return DurationField(self._video_track.duration / 1000)
        return DurationField(0)

    @property
    def resolution(self) -> str:
        if self._video_track:
            width = self._video_track.width
            height = self._video_track.height
            if width and height:
                return Resolution(width, height)
        return "Unknown"

    @property
    def video_codec(self) -> str:
        if self._video_track and self._video_track.format:
            return QuotedField(value=self._video_track.format)
        return QuotedField(value="Unknown")

    @property
    def audio_codec(self) -> str:
        if self._audio_track and self._audio_track.format:
            return QuotedField(value=self._audio_track.format)
        return QuotedField(value="Unknown")

    @property
    def frame_rate(self) -> str | None:
        if self._video_track and self._video_track.frame_rate:
            frame_rate_str = self._video_track.frame_rate
            frame_rate = float(frame_rate_str)
            return FrameRate(frame_rate)
        return None

    @property
    def bitrate(self) -> str | None:
        if self._video_track and self._video_track.overall_bit_rate:
            bps = self._video_track.overall_bit_rate
            return Bitrate(bps)
        return None

    @override
    def get_content_sections(self) -> list[Section]:
        video_info = Section("Video Information")
        video_info.add(LabelField("Duration", self.duration))
        video_info.add(LabelField("Resolution", self.resolution))
        video_info.add(LabelField("Codec", self.video_codec))
        if frame_rate := self.frame_rate:
            video_info.add(LabelField("Frame Rate", frame_rate))
        if bitrate := self.bitrate:
            video_info.add(LabelField("Bitrate", bitrate))
        yield video_info


class FileFactory:
    """Factory class for creating file objects"""

    @classmethod
    def from_path(cls, file_path: str) -> File:
        path = Path(file_path)

        if file := cls.match_special_file(path):
            return file
        else:
            return cls.match_regular_file(path)

    @classmethod
    def match_special_file(cls, path: Path) -> File:
        if path.is_symlink():
            return SymlinkFile(path=path)
        elif path.is_dir():
            return Directory(path=path)

    @classmethod
    def match_regular_file(cls, path: Path) -> File:
        mime = magic.from_file(path, mime=True)

        if cls.is_video_file(path, mime):
            file = VideoFile(path=path)
        elif cls.is_audio_file(path, mime):
            file = AudioFile(path=path)
        elif cls.is_image_file(path, mime):
            file = ImageFile(path=path)
        elif cls.is_plain_text_file(path, mime):
            file = TextFile(path=path)
        elif CodeFile.match(path=path):
            file = CodeFile(path=path)
        else:
            file = RegularFile(path=path)

        return file

    @classmethod
    def is_audio_file(cls, path: Path, mime: str) -> bool:
        return mime.startswith("audio/")

    @classmethod
    def is_video_file(cls, path: Path, mime: str) -> bool:
        return mime.startswith("video/")

    @classmethod
    def is_image_file(cls, path: Path, mime: str) -> bool:
        return mime.startswith("image/")

    @classmethod
    def is_plain_text_file(cls, path: Path, mime: str) -> bool:
        return mime == "text/plain"


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
        return NumberField(self._line_count)

    @property
    def word_count(self) -> int:
        return NumberField(self._word_count)

    @property
    def encoding(self) -> str:
        return QuotedField(value=self._encoding)

    @override
    def get_content_sections(self) -> list[Section]:
        text_info = Section("Content Information")
        text_info.add(LabelField("Encoding", self.encoding))
        text_info.add(LabelField("Lines", self.line_count))
        text_info.add(LabelField("Words", self.word_count))
        yield text_info

    @override
    def get_preview(self, max_lines=20):
        code = Code(self.path, max_lines=max_lines)
        preview_content = [code]
        if missing_lines := max(0, self._line_count - max_lines):
            preview_content.append(f"... +{missing_lines} lines")
        return Group(*preview_content)


@dataclass
class SymlinkFile(File):
    entity_type: str = "Symlink"
    icon: str = "🔗"

    @property
    def target(self) -> str:
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
        files = sum(1 for item in self._items if item.is_file())
        directories = sum(1 for item in self._items if item.is_dir())
        return DirectorySummary(directories=directories, files=files)

    @override
    def get_content_sections(self) -> list[Section]:
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

    @override
    def get_content_sections(self) -> list[Section]:
        code_info = Section("Code Information")
        code_info.add(LabelField("Language", self.language))
        code_info.add(LabelField("Encoding", self.encoding))
        code_info.add(LabelField("Lines", self.line_count))
        yield code_info
