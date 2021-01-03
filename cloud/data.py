import queue
import shelve
import asyncio
from pathlib import Path

from b2sdk.v1 import (
    InMemoryAccountInfo,
    B2Api,
    DownloadDestLocalFile,
    DoNothingProgressListener,
)
from PIL import Image

from . import paths, content_types

SHELVE = shelve.open(str(paths.shelve), writeback=True)
THUMB_MQ = queue.Queue()

BUCKET = None
B2API = None

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


async def download(file_id: str, path: str):
    global B2API
    download_dest = DownloadDestLocalFile(path)
    progress_listener = DoNothingProgressListener()
    B2API.download_file_by_id(file_id, download_dest, progress_listener)


async def convert_to_thumb(path: str):
    im = Image.open(path)
    im.thumbnail((128, 128), Image.ANTIALIAS)
    im.save(path, "JPEG")


async def generate_thumb(file_id: str):
    thumbnail = paths.thumbs.joinpath(file_id + ".jpg")
    await download(file_id, str(thumbnail))
    await convert_to_thumb(thumbnail)
    print(f"Generated {file_id}")


def ls(path) -> (list, list):
    idx = f"{BUCKET.name}/{path}"
    if idx in SHELVE:
        return SHELVE[idx]
    else:
        folders, files = [], []
        for file_info, folder_name in BUCKET.ls(str(path), show_versions=False):
            if folder_name is not None:
                folders.append(Folder(folder_name))
            else:
                files.append(File(file_info))
        SHELVE[idx] = (folders, files)
        SHELVE.sync()
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

    def get_thumbnail(self, queue):
        if self.type in content_types.video:
            self.thumbnail = "/static/icons/video.svg"
        elif self.type in content_types.images:
            thumbnail = paths.thumbs.joinpath(self.id + ".jpg")
            self.thumbnail = "/" + str(thumbnail.relative_to(paths.home))
            if not thumbnail.exists():
                shutil.copy(paths.static.joinpath("icons", "cache.png"), thumbnail)
                queue.put_nowait(self.id)
                


class Folder:
    def __init__(self, path):
        self.path = Path(path)
        self.name = self.path.name
        self.parent = self.path.parent


async def thumbnail_worker(queue):
    while True:
        if not queue.empty():
            file_id = await queue.get()
            await generate_thumb(file_id)
        await asyncio.sleep(5)

