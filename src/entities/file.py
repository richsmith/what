import grp
import os
import pwd
from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ..fields import FilePermissions, FileSize, SystemUser, Timestamp
from ..presentation import Field, Section
from .entity import Entity


@dataclass(kw_only=True)
class File(Entity):
    """Container for file information"""

    entity_type: str = "File"
    icon: str = "📄"
    path: Path

    def add_attribute(self, name: str, value: any) -> None:
        pass

    @property
    def name(self) -> Path:
        """Return the file name"""
        return f"[bold]{self.path.name}[/bold]"

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
        basic.add(Field("URI", f"file://{self.path}"))
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

    def get_sections(self) -> list[Section]:
        """Return sections for the image file presentation"""
        # Call the base class method to get common sections
        yield from super().get_sections()

        # Image-specific section
        image_info = Section("Image Information")
        image_info.add(Field("Dimensions", "1920 x 1080"))
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
        else:
            file = RegularFile(path=path)

        return file


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
