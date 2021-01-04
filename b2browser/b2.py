from pathlib import Path
from shelve import Shelf

import b2sdk.v1 as b2sdk

from . import console, paths, ls_cache


class __B2:
    def __init__(self):
        self.bucket = None
        self.api = None

    def setup(self, application_key_id: str, application_key: str, bucket_name: str):
        info = b2sdk.InMemoryAccountInfo()
        self.api = b2sdk.B2Api(info)
        self.api.authorize_account("production", application_key_id, application_key)
        self.bucket = self.api.get_bucket_by_name(bucket_name)

    def download(self, file_id: str, dest_path: str):
        download_dest = b2sdk.DownloadDestLocalFile(dest_path)
        progress_listener = b2sdk.DoNothingProgressListener()
        self.api.download_file_by_id(file_id, download_dest, progress_listener)

    def ls(self, path: str) -> (list, list):
        path = path.strip('/')
        console.log(f"[yellow]ls [/yellow] [green]{path}[/green]")

        if not ls_cache.is_cached_folder(path):
            folders, files = [], []
            for file_info, folder_path in self.bucket.ls(path, show_versions=False):
                if folder_path is None:
                    file_path = file_info.file_name
                    ls_cache.add(file_info)
                    files.append(file_path)
                else:
                    ls_cache.add(folder_path)
                    folders.append(folder_path)
            ls_cache.write_folder(path, folders, files)
        return ls_cache.ls(path)

    def cache(self, file_id: str, dest_path: str) -> str:
        cached_file = paths.data.joinpath(dest_path)
        if not cached_file.exists():
            cached_file.parent.mkdir(parents=True, exist_ok=True)
            self.download(file_id, cached_file)
        return f"/{cached_file.relative_to(paths.home)}"

B2 = __B2()







