import pytest
from unittest.mock import patch


from src.dogaas.downloader import TaskManager, DownloaderTask, DuplicateTaskError
import requests


class TestDownloaderTask:
    @staticmethod
    def test_raise_invalid_url():
        with pytest.raises(ValueError):
            DownloaderTask("invalid_url")


class TestTaskManager:
    @staticmethod
    def test_add_task():
        taskmanager = TaskManager()
        taskmanager.add_task("task_a", DownloaderTask("https://dummy_url_a"))
        assert taskmanager.tasks["task_a"].url == "https://dummy_url_a"
        with pytest.raises(DuplicateTaskError):
            taskmanager.add_task("task_a", DownloaderTask("https://dummy_url_a"))

    @staticmethod
    def test_remove_task():
        taskmanager = TaskManager()
        taskmanager.add_task("task_a", DownloaderTask("https://dummy_url_a"))
        taskmanager.remove_task("task_a")
        assert taskmanager.tasks.get("task_a") is None

    @staticmethod
    def test_rename_task():
        taskmanager = TaskManager()
        taskmanager.add_task("task_a", DownloaderTask("https://dummy_url_a"))
        taskmanager.rename_task("task_a", "task_A")
        assert taskmanager.tasks.get("task_a") is None
        assert taskmanager.tasks["task_A"].url == "https://dummy_url_a"

    @staticmethod
    def test_download(tmpdir):
        MOCK_URL = "https://httpbin.org"
        TASK_NAME = "task_a"
        taskmanager = TaskManager()
        taskmanager.add_task(TASK_NAME, DownloaderTask(MOCK_URL))
        # with patch("requests.get", return_value=1) as mock:
        #     response = requests.models.Response()
        #     response.request = requests.models.Request(url=MOCK_URL)
        #     response.status_code = 403
        #     mock.return_value = response
        #     with pytest.raises(requests.exceptions.HTTPError):
        taskmanager.download(TASK_NAME, tmpdir)
