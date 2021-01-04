from functools import partial
from pathlib import Path
from random import randint
import asyncio
import shelve
import shutil
from concurrent.futures import ThreadPoolExecutor

from rich.console import Console
from b2sdk.v1 import (
    InMemoryAccountInfo,
    B2Api,
    DownloadDestLocalFile,
    DoNothingProgressListener,
)
from PIL import Image

from . import paths, content_types, utils


_executor = ThreadPoolExecutor(16)

console = Console()

SHELVE = shelve.open(str(paths.shelve), writeback=True)

BUCKET = None
B2API = None


def set_bucket(bucket_name: str, application_key_id: str, application_key: str):
    global BUCKET, B2API
    info = InMemoryAccountInfo()
    B2API = B2Api(info)
    B2API.authorize_account("production", application_key_id, application_key)
    BUCKET = B2API.get_bucket_by_name(bucket_name)


def download(file_id: str, path: str):
    global B2API
    download_dest = DownloadDestLocalFile(path)
    progress_listener = DoNothingProgressListener()
    B2API.download_file_by_id(file_id, download_dest, progress_listener)


def convert_to_thumb(path: str):
    im = Image.open(path)
    o_width, o_height = 200, 150
    factor = max(o_width / im.width, o_height / im.height)
    width, height = round(im.width * factor), round(im.height * factor)
    im = im.resize((width, height), resample=Image.LANCZOS)
    im.save(path, "JPEG")


def generate_thumb(file_id: str):
    thumbnail = paths.thumbs.joinpath(file_id + ".jpg")
    download(file_id, str(thumbnail))
    convert_to_thumb(thumbnail)


def is_file(path: str):
    return path in SHELVE and isinstance(SHELVE[path], File)


def ls(path: str) -> (list, list):
    path = path.strip('/')
    console.log(f"[yellow]ls [/yellow] [green]{path}[/green]")
    if path in SHELVE and not SHELVE[path].is_empty():
        return SHELVE[path]
    else:
        folders, files = [], []
        for file_info, folder_path in BUCKET.ls(path, show_versions=False):
            if folder_path is not None:
                if not folder_path in SHELVE:
                    SHELVE[folder_path] = Folder(folder_path)
                    console.log(f"[yellow]append folder[/yellow] [green]{folder_path}[/green]")
                folders.append(folder_path)
            else:
                file_path = file_info.file_name
                if not file_path in SHELVE:
                    SHELVE[file_path] = File(file_info)
                    console.log(f"[yellow]shelve[/yellow] [green]{file_path}[/green]")
                files.append(file_path)
        SHELVE[path] = Folder(path, folders, files)
        SHELVE.sync()
        return SHELVE[path]


def cache_file(path: str):
    file = SHELVE[path]
    target = paths.data.joinpath(file.path)
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        download(file.id, target)
    return "/" + str(target.relative_to(paths.home))


class File:
    def __init__(self, file_info):
        _path = Path(file_info.file_name)
        self.path = str(_path)
        self.name = _path.name
        self.parent = str(_path.parent)
        self.hash = file_info.content_md5
        self.type = file_info.content_type
        self.size = utils.humanize_bytes(file_info.size)
        self.id = file_info.id_


class Folder:
    def __init__(self, path, folders=[], files=[]):
        _path = Path(path)
        self.path = str(_path)
        self.name = _path.name
        self.parent = str(_path.parent)
        self.folders = folders
        self.files = files

    def is_empty(self):
        return len(self.folders) == len(self.files) == 0

    def flatten(self):
        folders = [SHELVE[f] for f in self.folders]
        files = [SHELVE[f] for f in self.files]
        return folders, files



def queue_thumbnails(files, queue):
    for file in files:
        if hasattr(file, "thumbnail"):
            continue

        if file.type in content_types.video:
            file.thumbnail = "/static/icons/video.svg"
        elif file.type in content_types.images:
            file.thumbnail = "/static/icons/cache.svg"
            queue.put_nowait(file.path)
        
        if hasattr(file, "thumbnail"):
            file.thumb_ext = Path(file.thumbnail).suffix[1:]


async def thumbnail_worker(name, queue):
    while True:
        file_path = await queue.get()
        file = SHELVE[file_path]
        console.log(
            f"[yellow]{name}[/yellow] [green]{queue.qsize()}[/green] [yellow]remaining[/yellow]"
        )
        loop = asyncio.get_event_loop()
        # For now the thumbnail generator is synchronous
        await loop.run_in_executor(_executor, partial(generate_thumb, file.id))
        file.thumbnail = "/" + str(paths.thumbs.joinpath(file.id + ".jpg").relative_to(paths.home))
        file.thumb_ext = "jpg"
        SHELVE[file_path] = file

