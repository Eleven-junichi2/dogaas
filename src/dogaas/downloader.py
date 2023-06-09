from dataclasses import dataclass
from typing import Callable, Optional
import abc
import re


def is_url(url: str, raise_if_not=False) -> bool:
    if re.match(r"^https?://", url):
        return True
    else:
        if raise_if_not:
            raise ValueError(f"`{url}` is not a valid URL")
        return False


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
        self,
        name: str,
        task: DownloaderTask,
    ):
        if isinstance(task, DownloaderTask):
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

    def download(self, task_name: str):
        if isinstance(task_name, str):
            if self.on_download:
                self.on_download()
        else:
            raise TypeError("`task_name` must be `str`")


class Downloader:
    def __init__(self, task_manager: Optional[TaskManager] = None):
        """
        Args:
            task_manager (Optional[None]):
        """
        if task_manager is None:
            task_manager = TaskManager()
        self._task_manager = task_manager

    @property
    def task_manager(self) -> TaskManager:
        return self.task_manager

    @property
    def tasks(self) -> Tasks:
        return self.task_manager.tasks
