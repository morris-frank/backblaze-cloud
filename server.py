import asyncio
from concurrent.futures import ThreadPoolExecutor

from sanic import Sanic
from sanic import response
from sanic_jinja2 import SanicJinja2
from sanic_httpauth import HTTPBasicAuth

import b2browser
import config

app = Sanic("b2browser")
app.static("/static", "./static")
auth = HTTPBasicAuth()
jinja = SanicJinja2(app, pkg_name="b2browser")

b2browser.B2.setup(
    config.application_key_id, config.application_key, config.bucket_name
)


@auth.verify_password
def verify_password(username, password):
    return (
        username == config.username
        and b2browser.utils.hash_password(config.app_salt, password) == config.password
    )


@app.listener("after_server_start")
def create_task_queue(app, loop):
    app.thumbnail_queue = asyncio.LifoQueue(maxsize=400)
    app.thread_executor = ThreadPoolExecutor(config.thread_pool_size)

    for i in range(config.thread_pool_size):
        app.add_task(
            b2browser.preview.worker(
                f"thumbnail_{i}", app.thumbnail_queue, app.thread_executor
            )
        )


@jinja.template("file.html")
async def single(request, path):
    file = b2browser.LS_CACHE[path]
    src = b2browser.B2.cache(file.id, file.path)
    return {
        "src": src,
        "file": file,
        "breadcrumb": b2browser.utils.make_crumbs(path),
    }


@jinja.template("folder.html")
async def folder(request, path):
    folders, files = b2browser.B2.ls(path)
    b2browser.preview.queue(files, request.app.thumbnail_queue)
    return {
        "folders": folders,
        "files": files,
        "breadcrumb": b2browser.utils.make_crumbs(path),
    }


@app.route("/")
@auth.login_required
async def root(request):
    return await folder(request, "")


@app.route("/<path:path>")
@auth.login_required
async def non_root(request, path: str):
    if b2browser.ls_cache.is_file(path):
        return await single(request, path)
    else:
        return await folder(request, path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
