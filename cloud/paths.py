from pathlib import Path

home = Path(__file__).parent.parent

static = home.joinpath("static")

thumbs = static.joinpath("thumbnails")
thumbs.mkdir(exist_ok=True)

data = static.joinpath("data")
data.mkdir(exist_ok=True)

cache = home.joinpath(".cache")
cache.mkdir(exist_ok=True)

shelve = cache.joinpath("shelve")
