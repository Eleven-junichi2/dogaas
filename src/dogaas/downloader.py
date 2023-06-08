from dataclasses import dataclass
import abc
from typing import Optional


@dataclass
class DownloaderTask:
    url: str


Tasks = dict[str, DownloaderTask]


class TaskDatabaseInterface(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def add_task(self, task: DownloaderTask):
        raise NotImplementedError

    @abc.abstractmethod
    def remove_task(self, task_identifier):
        raise NotImplementedError


class TaskManager(TaskDatabaseInterface):
    def __init__(self, **tasks: dict[str, DownloaderTask]):
        self.tasks: Tasks = {}
        for name, task in tasks.items():
            self.add_task(name, task)

    def add_task(
        self,
        name: str,
        task: DownloaderTask,
    ):
        if isinstance(task, DownloaderTask):
            self.tasks[name] = task
        else:
            raise TypeError("`task` must be `DownloaderTask`")

    def rename_task(self, task_name: str, new_name: str):
        if isinstance(task_name, str):
            self.tasks[new_name] = self.tasks.pop(task_name)
        else:
            raise TypeError("`task_name` must be a `str`")

    def remove_task(self, task_name: str):
        if isinstance(task_name, str):
            self.tasks.pop(task_name)
        else:
            raise TypeError("`task_name` must be `str`")

    def download(self, task_name: str):
        if isinstance(task_name, str):
            raise NotImplementedError
        else:
            raise TypeError("`task_name` must be `str`")


class Downloader:
    def __init__(self, task_manager: Optional[None] = None):
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
