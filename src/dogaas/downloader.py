from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse, unquote
from typing import Callable, Optional
import abc
import re

import requests


def is_url(url: str, raise_if_not=False) -> bool:
    if re.match(r"^https?://", url):
        return True
    else:
        if raise_if_not:
            raise ValueError(f"`{url}` is not a valid URL")
        return False


class DuplicateTaskError(Exception):
    pass


@dataclass
class DownloaderTask:
    _url: str

    @property
    def url(self) -> str:
        is_url(self._url, raise_if_not=True)
        return self._url

    def __post_init__(self):
        is_url(self.url, raise_if_not=True)

    def rewrite_url(self, new_url: str):
        if is_url(new_url, raise_if_not=True):
            self._url = new_url


Tasks = dict[str, DownloaderTask]


class TaskDatabaseInterface(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def add_task(self, task: DownloaderTask):
        raise NotImplementedError

    @abc.abstractmethod
    def remove_task(self, task_identifier):
        raise NotImplementedError


class TaskManager(TaskDatabaseInterface):
    def __init__(
        self,
        tasks: Optional[dict[str, DownloaderTask]] = None,
        on_add: Optional[Callable[..., None]] = None,
        on_remove: Optional[Callable[..., None]] = None,
        on_rename: Optional[Callable[..., None]] = None,
        on_download: Optional[Callable[..., None]] = None,
    ):
        self.tasks: Tasks = {}
        self.on_add = on_add
        self.on_remove = on_remove
        self.on_rename = on_rename
        self.on_download = on_download
        if tasks:
            for name, task in tasks.items():
                self.add_task(name, task)

    def add_task(
        self, name: str, task: DownloaderTask, raise_if_duplicate: bool = False
    ):
        if isinstance(task, DownloaderTask):
            if self.tasks.get(name, False):
                raise DuplicateTaskError(f"task `{name}` already exists")
            self.tasks[name] = task
            if self.on_add:
                self.on_add()
        else:
            raise TypeError("`task` must be `DownloaderTask`")

    def rename_task(self, task_name: str, new_name: str):
        if isinstance(task_name, str):
            self.tasks[new_name] = self.tasks.pop(task_name)
            if self.on_rename:
                self.on_rename()
        else:
            raise TypeError("`task_name` must be a `str`")

    def remove_task(self, task_name: str):
        if isinstance(task_name, str):
            self.tasks.pop(task_name)
            if self.on_remove:
                self.on_remove()
        else:
            raise TypeError("`task_name` must be `str`")

    def download(
        self, task_name: str, dirpath_for_dest: Path | str, yield_progress=True
    ) -> None | float:
        if isinstance(task_name, str):
            url = self.tasks[task_name].url
            dlfile_name = self.filename_from_url(url)
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                file_size = int(response.headers.get("Content-Length"))
                progress = 0
                with open(Path(dirpath_for_dest) / dlfile_name, "wb") as file:
                    chunk_size = 1024
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        progress += len(chunk)
                        file.write(chunk)
                        if yield_progress:
                            yield progress / file_size
            if self.on_download:
                self.on_download()
        else:
            raise TypeError("`task_name` must be `str`")

    def filename_from_url(self, url: str) -> str:
        return unquote(Path(urlparse(url).path).name)
