import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

from sanic import Sanic, response
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
def create_task_queues(app, loop):
    app.threaded_executor = ThreadPoolExecutor(config.thread_pool_size)

    app.updates_queue = asyncio.Queue(maxsize=1_000)
    app.ls_queue = asyncio.LifoQueue(maxsize=100)
    app.add_task(b2browser.b2.worker(
        f"ls_worker", app.ls_queue, app.updates_queue, jinja
    ))

    app.preview_queue = asyncio.LifoQueue(maxsize=10_000)
    for i in range(config.thread_pool_size):
        app.add_task(
            b2browser.preview.worker(
                f"preview_worker_{i}", app.threaded_executor, app.preview_queue, app.updates_queue
            )
        )


@jinja.template("single.html")
async def single(request, path):
    file = b2browser.LS_CACHE[path]
    src = b2browser.B2.cache(file.id, file.path)
    return {
        "src": src,
        "file": file,
        "breadcrumb": b2browser.utils.make_crumbs(path),
        "path": path
    }


@jinja.template("folder.html")
async def folder(request, path):
    folders, files = b2browser.B2.ls(path)
    b2browser.preview.put(files, request.app.preview_queue)
    return {
        "folders": folders,
        "files": files,
        "breadcrumb": b2browser.utils.make_crumbs(path),
        "path": path
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


@app.websocket('/updates')
async def updates_out(request, ws):
    while True:
        update = await request.app.updates_queue.get()
        # b2browser.console.log(f"[yellow]Sending:[/yellow] [green]{update}[/green]")
        await ws.send(json.dumps(update))


@app.websocket('/update')
async def updates_in(request, ws):
    while True:
        data = await ws.recv()
        data = json.loads(data)

        b2browser.console.log(f"[yellow]Wants:[/yellow] [green]{data}[/green]")
        if data["type"] == "folder":
            app.ls_queue.put_nowait(data["path"])



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
