import grp
import os
import pwd
from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image

from ..fields import (
    Code,
    EntityName,
    Field,
    FilePermissions,
    FileSize,
    ImageDimensions,
    PathUri,
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
        return EntityName(self.path.name)

    @property
    def size(self) -> FileSize:
        """Return the file size"""
        return FileSize(self._stat.st_size)

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
            return SystemUser(pwd.getpwuid(self._stat.st_uid).pw_name)
        except KeyError:
            return SystemUser(str(self._stat.st_uid))

    @property
    def user_group(self) -> SystemUser:
        """Return the file group"""
        try:
            return SystemUser(grp.getgrgid(self._stat.st_gid).gr_name)
        except KeyError:
            return SystemUser(str(self._stat.st_gid))

    def get_sections(self) -> list[Section]:
        """Return sections for the file presentation"""

        basic = Section("File")
        basic.add(Field("Name", self.name))
        self.add_path_fields(basic)
        basic.add(Field("URI", PathUri(self.path)))
        basic.add(Field("Size", self.size))
        basic.add(Field("Type", self.entity_type))
        yield basic

        ownership = Section("Permissions")
        ownership.add(Field("Owner", self.owner))
        ownership.add(Field("Group", self.user_group))
        ownership.add(Field("Permissions", self.permissions))
        yield ownership

        timestamps = Section("Timestamps")
        timestamps.add(Field("Created", self.created))
        timestamps.add(Field("Modified", self.modified))
        timestamps.add(Field("Accessed", self.accessed))
        yield timestamps

    def add_path_fields(self, section):
        section.add(Field("Path", self.path))


@dataclass
class ImageFile(File):
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

    def get_sections(self) -> list[Section]:
        """Return sections for the image file presentation"""
        # Call the base class method to get common sections
        yield from super().get_sections()

        # Image-specific section
        image_info = Section("Image Information")
        image_info.add(Field("Dimensions", self.dimensions))
        yield image_info


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
        else:
            file = CodeFile(path=path)

        return file

    @staticmethod
    def is_image_file(file_path: str) -> bool:
        """Check if the file is an image file"""
        # FIXME testing
        return file_path.name.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))


@dataclass
class RegularFile(ABC, File):
    pass


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
        section.add(Field("Link", "↪️ " + self.target))


@dataclass
class Directory(File):
    entity_type: str = "Directory"
    icon: str = "📁"


@dataclass
class CodeFile(RegularFile):

    @property
    def language(self) -> str:
        """Return the programming language of the code file"""
        # Placeholder for actual language detection logic
        return "Python"

    @property
    def code(self) -> str:
        """Return the code content"""
        return Code(self.path)

    def get_sections(self) -> list[Section]:
        """Return sections for the code file presentation"""
        # Call the base class method to get common sections
        yield from super().get_sections()

        yield self.code
