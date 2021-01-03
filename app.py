from sanic import Sanic
from sanic_jinja2 import SanicJinja2

import cloud
import config

app = Sanic("cloud")
app.static("/static", "./static")
jinja = SanicJinja2(app, pkg_name="cloud")

cloud.set_bucket(config.bucket_name, config.application_key_id, config.application_key)


@app.route("/")
@jinja.template("folder.html")
async def index(request):
    folders, files = cloud.ls("")
    return {"folders": folders, "files": files}


@app.route("/<path:path>")
@jinja.template("folder.html")
async def index(request, path: str):
    folders, files = cloud.ls(path)
    return {
        "folders": folders,
        "files": files,
        "breadcrumb": cloud.utils.make_crumbs(path),
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
