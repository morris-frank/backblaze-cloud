from pathlib import Path

home = Path(__file__).parent.parent

static = home.joinpath("static")

thumbnail = static.joinpath("thumbnails")
thumbnail.mkdir(exist_ok=True)

data = static.joinpath("data")
data.mkdir(exist_ok=True)

cache = home.joinpath(".cache")
cache.mkdir(exist_ok=True)

ls_cache = cache.joinpath("ls_cache")

thumbnail_cache = cache.joinpath("thumbnails")
thumbnail_cache.mkdir(exist_ok=True)
