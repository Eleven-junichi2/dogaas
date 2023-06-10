from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse, unquote
from typing import Callable, Optional
import abc
import re

from serde import serialize, deserialize
from serde.json import from_json, to_json
import requests


def is_url(url: str, raise_if_not=False) -> bool:
    if re.match(r"^https?://", url):
        return True
    else:
        if raise_if_not:
            raise ValueError(f"`{url}` is not a valid URL")
        return False


def filename_from_url(url: str) -> str:
    return unquote(Path(urlparse(url).path).name)


class DuplicateTaskError(Exception):
    pass


@deserialize
@serialize
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
    ):
        self.tasks: Tasks = {}
        self.on_add = on_add
        self.on_remove = on_remove
        self.on_rename = on_rename
        if tasks:
            for name, task in tasks.items():
                self.add_task(name, task)

    def add_task(
        self, name: str, task: DownloaderTask, raise_if_duplicate: bool = False
    ):
        if isinstance(task, DownloaderTask):
            if self.tasks.get(name, False) and raise_if_duplicate:
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
        """remove task

        Args:
            task_name (str):

        Raises:
            TypeError:
            KeyError:
        """
        if isinstance(task_name, str):
            self.tasks.pop(task_name)
            if self.on_remove:
                self.on_remove()
        else:
            raise TypeError("`task_name` must be `str`")

    def make_downloader_from_task(self, task_name: str) -> "Downloader":
        """Try to request content to download by task then return `Downloader`."""
        if isinstance(task_name, str):
            response = requests.get(self.tasks[task_name].url, stream=True)
            return Downloader(response)
        else:
            raise TypeError("`task_name` must be `str`")

    def save_tasks_to_json(
        self, dirpath_for_dest: Path | str, filename_without_ext_str: str
    ):
        with open(
            Path(dirpath_for_dest).absolute() / f"{filename_without_ext_str}.json", "w"
        ) as f:
            f.write(to_json(self.tasks))

    def load_tasks_from_json(self, filepath: Path | str):
        if not Path(filepath).exists():
            raise FileNotFoundError()
        with open(Path(filepath), encoding="utf-8") as f:
            self.tasks = from_json(dict[str, DownloaderTask], f.read())


class Downloader:
    def __init__(self, response: requests.Response):
        self._response = response

    @property
    def response(self) -> requests.Response:
        return self._response

    def get_filesize_str(self) -> str:
        return self.response.headers.get("Content-Length", 0)

    def download(
        self, dirpath_for_dest: Path | str, chunk_size=1024, yield_progress=True
    ) -> None | float:
        dlfile_name = filename_from_url(self.response.url)
        progress = 0
        with open(Path(dirpath_for_dest).absolute() / dlfile_name, "wb") as file:
            for chunk in self.response.iter_content(chunk_size=chunk_size):
                progress += len(chunk)
                file.write(chunk)
                if yield_progress:
                    yield progress
