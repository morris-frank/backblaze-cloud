from pathlib import Path

__all__ = ["home_path", "SHELVE_PATH", "THUMB_PATH"]

home_path = Path(__file__).parent.parent

cache_path = home_path.joinpath(".cache")
cache_path.mkdir(exist_ok=True)

THUMB_PATH = home_path.joinpath("static", "thumbnails")
THUMB_PATH.mkdir(exist_ok=True)

SHELVE_PATH = cache_path.joinpath("shelve")
