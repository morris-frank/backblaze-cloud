import shelve
from pathlib import Path
from b2sdk.v1 import (
    InMemoryAccountInfo,
    B2Api,
    DownloadDestLocalFile,
    DoNothingProgressListener,
)
from PIL import Image

from .settings import SHELVE_PATH, THUMB_PATH, home_path

__all__ = ["File", "Folder", "ls", "set_bucket"]

SHELVE = shelve.open(str(SHELVE_PATH))
BUCKET = None
B2API = None

IMG_TYPES = "image/jpeg"
VIDEO_TYPES = "video/mp4"


def set_bucket(bucket_name: str, application_key_id: str, application_key: str):
    global BUCKET, B2API
    info = InMemoryAccountInfo()
    B2API = B2Api(info)
    B2API.authorize_account("production", application_key_id, application_key)
    BUCKET = B2API.get_bucket_by_name(bucket_name)


def humanize_bytes(size: int) -> str:
    if size < 0.5e6:
        return f"{size/1e3:.1f}Kb"
    elif size < 0.5e9:
        return f"{size/1e6:.1f}Mb"
    else:
        return f"{size/1e9:.1f}Gb"


def download(file_id: str, path: str):
    global B2API
    download_dest = DownloadDestLocalFile(path)
    progress_listener = DoNothingProgressListener()
    B2API.download_file_by_id(file_id, download_dest, progress_listener)


def convert_to_thumb(path: str):
    im = Image.open(path)
    im.thumbnail((128, 128), Image.ANTIALIAS)
    im.save(path, "JPEG")
    print(f"Thumbed {path}")


def ls(path) -> (list, list):
    idx = f"{BUCKET.name}/{path}"
    if idx in SHELVE:
        return SHELVE[idx]
    else:
        print(f"{idx} not in shelve")
        folders, files = [], []
        for file_info, folder_name in BUCKET.ls(str(path), show_versions=False):
            if folder_name is not None:
                folders.append(Folder(folder_name))
            else:
                files.append(File(file_info))
        SHELVE[idx] = (folders, files)
        return SHELVE[idx]


class File:
    def __init__(self, file_info):
        self.path = Path(file_info.file_name)
        self.name = self.path.name
        self.parent = self.path.parent
        self.hash = file_info.content_md5
        self.type = file_info.content_type
        self.size = humanize_bytes(file_info.size)
        self.id = file_info.id_

        if self.type in IMG_TYPES:
            self.gen_thumb()
        elif self.type in VIDEO_TYPES:
            self.thumbnail = "/static/icons/video.svg"

    def gen_thumb(self):
        thumbnail = THUMB_PATH.joinpath(self.id + ".jpg")
        if not thumbnail.exists():
            download(self.id, str(thumbnail))
            convert_to_thumb(thumbnail)
        self.thumbnail = "/" + str(thumbnail.relative_to(home_path))


class Folder:
    def __init__(self, path):
        self.path = Path(path)
        self.name = self.path.name
        self.parent = self.path.parent
