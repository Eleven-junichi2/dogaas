import pytest

# from unittest.mock import patch


from src.dogaas.downloader import TaskManager, DownloaderTask, DuplicateTaskError

# import requests


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
            taskmanager.add_task(
                "task_a", DownloaderTask("https://dummy_url_a"), raise_if_duplicate=True
            )

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
    def test_save_tasks_to_json(tmpdir):
        taskmanager = TaskManager()
        taskmanager.add_task("task_a", DownloaderTask("https://dummy_url_a"))
        taskmanager.save_tasks_to_json(tmpdir, "test")

    @staticmethod
    def test_load_tasks_from_json(tmpdir):
        taskmanager = TaskManager()
        taskmanager.add_task("task_a", DownloaderTask("https://dummy_url_a"))
        taskmanager.save_tasks_to_json(tmpdir, "test")
        taskmanager.load_tasks_from_json(tmpdir.join("test.json"))
        with pytest.raises(FileNotFoundError):
            taskmanager.load_tasks_from_json(tmpdir.join("invalidfilename"))
