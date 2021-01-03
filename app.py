from sanic import Sanic
from sanic_jinja2 import SanicJinja2
import asyncio

import cloud
import config

app = Sanic("cloud")

app.static("/static", "./static")

jinja = SanicJinja2(app, pkg_name="cloud")

cloud.set_bucket(config.bucket_name, config.application_key_id, config.application_key)


@app.listener('after_server_start')
def create_task_queue(app, loop):
    app.thumbnail_queue = asyncio.Queue(maxsize=1_000)
    app.add_task(cloud.data.thumbnail_worker(app.thumbnail_queue))


@app.route("/")
@jinja.template("folder.html")
async def index(request):
    folders, files = cloud.ls("")
    return {"folders": folders, "files": files}


@app.route("/<path:path>")
@jinja.template("folder.html")
async def folder(request, path: str):
    folders, files = cloud.ls(path)
    for file in files:
        file.get_thumbnail(request.app.thumbnail_queue)
    return {
        "folders": folders,
        "files": files,
        "breadcrumb": cloud.utils.make_crumbs(path),
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
