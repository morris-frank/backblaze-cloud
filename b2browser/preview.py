import asyncio
from functools import partial
from pathlib import Path

from PIL import Image

from . import paths, ls_cache, console, B2


thumbnail_size = (200, 150)


def preview_path(file_id: str) -> Path:
    return paths.thumbnail.joinpath(f"{file_id}.jpg")


def preview_uri(file_id: str) -> str:
    return f"/{preview_path(file_id).relative_to(paths.home)}"


class VideoPreview:
    types = ("video/mp4", "video/quicktime")
    default = "/static/icons/video.svg"


class ImagePreview:
    types = ("image/jpeg",)
    default = "/static/icons/cache.svg"

    def make_preview(input_path: Path, output_path: Path):
        im = Image.open(input_path)
        factor = max(thumbnail_size[0] / im.width, thumbnail_size[1] / im.height)
        width, height = round(im.width * factor), round(im.height * factor)
        im = im.resize((width, height), resample=Image.LANCZOS)
        im.save(output_path, "JPEG")


preview_types = {"image": ImagePreview, "video": VideoPreview}


def determine_preview_type(content_type: str):
    for name, preview in preview_types.items():
        if content_type in preview.types:
            return name


def default_preview(preview_type: str):
    return preview_types[preview_type].default


def make_preview(file_path: str):
    file = ls_cache.LS_CACHE[file_path]
    preview = preview_types[file.preview_type]

    if hasattr(preview, "make_preview"):
        # Download the file to the local thumbnail cache folder
        cached_file = paths.thumbnail_cache.joinpath(file.id)
        B2.download(file.id, str(cached_file))

        preview.make_preview(cached_file, preview_path(file.id))

        # Delete the cached downloaded file
        cached_file.unlink()

        file.thumbnail = preview_uri(file.id)
    else:
        file.thumbnail = preview.default


def queue(files, queue):
    for file in files:
        # This file has a cached preview
        if not file.waiting_for_preview:
            continue

        # This file was waiting for a preview but its here now
        if preview_path(file.id).exists():
            file.waiting_for_preview = False
            file.thumbnail = preview_uri(file.id)
            continue

        file.preview_type = determine_preview_type(file.type)
        file.thumbnail = default_preview(file.preview_type)

        queue.put_nowait(file.path)


async def worker(name: str, queue, executor):
    while True:
        file_path = await queue.get()

        # For now the thumbnail generator is synchronous
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(executor, partial(make_preview, file_path))

        console.log(
            f"[yellow]{name}[/yellow] [green]{queue.qsize()}[/green] [yellow]remain[/yellow]"
        )
