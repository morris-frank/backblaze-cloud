import asyncio
from functools import partial
from pathlib import Path

from PIL import Image

from . import paths, ls_cache, console, B2


preview_size = (200, 150)


def preview_path(file_id: str) -> Path:
    return paths.previews.joinpath(f"{file_id}.jpg")


def preview_url(file_id: str) -> str:
    return f"/{preview_path(file_id).relative_to(paths.home)}"


class VideoPreview:
    types = ("video/mp4", "video/quicktime")
    default = "/static/icons/video.svg"


class ImagePreview:
    types = ("image/jpeg", "image/png")
    default = "/static/icons/cache.svg"

    @staticmethod
    def make_preview(input_path: Path, output_path: Path):
        im = Image.open(input_path)
        factor = max(preview_size[0] / im.width, preview_size[1] / im.height)
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


def make_preview(file_path: str, updates_queue: asyncio.Queue):
    file = ls_cache.LS_CACHE[file_path]
    if file.preview_type not in preview_types:
        return

    preview = preview_types[file.preview_type]

    if preview_path(file.id).exists():
        return

    if hasattr(preview, "make_preview"):
        # Download the file to the local previw cache folder
        cached_file = paths.preview_cache.joinpath(f"{file.id}{file.ext}")
        B2.download(file.id, str(cached_file))

        preview.make_preview(cached_file, preview_path(file.id))

        # Delete the cached downloaded file
        cached_file.unlink()

        file.preview_url = preview_url(file.id)
        updates_queue.put_nowait(
            {"type": "preview", "id": file.id, "url": file.preview_url}
        )
    else:
        file.preview_url = preview.default


def put(files, queue: asyncio.Queue):
    for file in files:
        # This file has a cached preview
        if not file.waiting_for_preview:
            continue

        # This file was waiting for a preview but its here now
        if preview_path(file.id).exists():
            file.waiting_for_preview = False
            file.preview_url = preview_url(file.id)
            continue

        file.preview_type = determine_preview_type(file.type)
        if file.preview_type in preview_types:
            file.preview_url = default_preview(file.preview_type)

            queue.put_nowait(file.path)


async def worker(
    name: str, executor, queue_in: asyncio.Queue, queue_out: asyncio.Queue
):
    while True:
        file_path = await queue_in.get()

        # For now the preview generator is synchronous
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            executor, partial(make_preview, file_path, queue_out)
        )

        console.log(
            f"[yellow]{name}[/yellow] [green]{queue_in.qsize()}[/green] [yellow]remain[/yellow]"
        )
