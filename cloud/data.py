import queue
from random import randint
import shelve
import asyncio
from pathlib import Path
import shutil
from functools import partial

from rich.console import Console
from b2sdk.v1 import (
    InMemoryAccountInfo,
    B2Api,
    DownloadDestLocalFile,
    DoNothingProgressListener,
)
from PIL import Image

from . import paths, content_types

from concurrent.futures import ThreadPoolExecutor


_executor = ThreadPoolExecutor(16)

console = Console()

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


def download(file_id: str, path: str):
    global B2API
    download_dest = DownloadDestLocalFile(path)
    progress_listener = DoNothingProgressListener()
    B2API.download_file_by_id(file_id, download_dest, progress_listener)


def convert_to_thumb(path: str):
    im = Image.open(path)
    im.thumbnail((128, 128), Image.ANTIALIAS)
    im.save(path, "JPEG")


def generate_thumb(file_id: str):
    thumbnail = paths.thumbs.joinpath(file_id + ".jpg")
    download(file_id, str(thumbnail))
    convert_to_thumb(thumbnail)


def is_file(path: str):
    return path in SHELVE


def ls(path: str) -> (list, list):
    idx = f"{BUCKET.name}/{path}"
    if idx in SHELVE:
        return SHELVE[idx]
    else:
        folders, files = [], []
        for file_info, folder_name in BUCKET.ls(str(path), show_versions=False):
            if folder_name is not None:
                folders.append(Folder(folder_name))
            else:
                file = File(file_info)
                SHELVE[str(file.path)] = file
                files.append(file)
        SHELVE[idx] = (folders, files)
        SHELVE.sync()
        return SHELVE[idx]

def cache_file(path: str):
    file = SHELVE[path]
    target = paths.data.joinpath(file.path)
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        download(file.id, target)
    return "/" + str(target.relative_to(paths.home))


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


async def thumbnail_worker(name, queue):
    while True:
        file_id = await queue.get()
        console.log(f"[yellow]{name}[/yellow] [green]{queue.qsize()}[/green] [yellow]remaining[/yellow]")
        loop = asyncio.get_event_loop()
        # For now the thumbnail generator is synchronous
        await loop.run_in_executor(_executor, partial(generate_thumb, file_id))

