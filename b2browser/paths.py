from pathlib import Path

home = Path(__file__).parent.parent

static = home.joinpath("static")

previews = static.joinpath("previews")
previews.mkdir(exist_ok=True)

data = static.joinpath("data")
data.mkdir(exist_ok=True)

cache = home.joinpath(".cache")
cache.mkdir(exist_ok=True)

ls_cache = cache.joinpath("ls_cache")

preview_cache = cache.joinpath("previews")
preview_cache.mkdir(exist_ok=True)
