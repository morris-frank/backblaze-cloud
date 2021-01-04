import asyncio

from sanic import Sanic
from sanic import response
from sanic_jinja2 import SanicJinja2

import cloud
import config

app = Sanic("cloud")
app.static("/static", "./static")
jinja = SanicJinja2(app, pkg_name="cloud")

cloud.set_bucket(config.bucket_name, config.application_key_id, config.application_key)


@app.listener("after_server_start")
def create_task_queue(app, loop):
    app.thumbnail_queue = asyncio.LifoQueue(maxsize=1_000)

    for i in range(16):
        app.add_task(cloud.data.thumbnail_worker(f"thumbnail_{i}", app.thumbnail_queue))


@jinja.template("file.html")
async def single(request, path):
    src = cloud.data.cache_file(path)
    return {
        "src": src,
        "breadcrumb": cloud.utils.make_crumbs(path),
    }


@jinja.template("folder.html")
async def folder(request, path):
    folder = cloud.ls(path)
    folders, files = folder.flatten()
    cloud.data.queue_thumbnails(files, request.app.thumbnail_queue)
    return {
        "folders": folders,
        "files": files,
        "breadcrumb": cloud.utils.make_crumbs(path),
    }


@app.route("/")
async def root(request):
    return await folder(request, "")


@app.route("/<path:path>")
async def non_root(request, path: str):
    if cloud.data.is_file(path):
        return await single(request, path)
    else:
        return await folder(request, path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
