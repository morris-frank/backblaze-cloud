from typing import Union
import shelve

from . import paths, utils


LS_CACHE = shelve.open(str(paths.ls_cache), writeback=True)


class File:
    def __init__(self, file_info):
        self.path = file_info.file_name
        self.name = self.path.split("/")[-1]
        self.hash = file_info.content_md5
        self.type = file_info.content_type
        self.size = utils.humanize_bytes(file_info.size)
        self.id = file_info.id_

        # Settings for the preview
        self.waiting_for_preview = True


class Folder:
    def __init__(self, path: str, folders=[], files=[]):
        self.path = path.strip("/")
        self.name = self.path.split("/")[-1]
        self.folders = folders
        self.files = files

    def is_empty(self):
        return len(self.folders) == len(self.files) == 0


def add(item: Union[File, Folder]):
    if isinstance(item, str):
        if not item in LS_CACHE:
            LS_CACHE[item] = Folder(item)
        # Is folder
    else:
        file_path = item.file_name
        if not file_path in LS_CACHE:
            LS_CACHE[file_path] = File(item)


def write_folder(path, folders, files):
    LS_CACHE[path] = Folder(path, folders, files)
    LS_CACHE.sync()


def ls(path: str):
    folder = LS_CACHE[path]
    folders = [LS_CACHE[f] for f in folder.folders]
    files = [LS_CACHE[f] for f in folder.files]
    return folders, files


def is_file(path: str):
    return path in LS_CACHE and isinstance(LS_CACHE[path], File)


def is_cached_folder(path: str):
    return path in LS_CACHE and not LS_CACHE[path].is_empty()
