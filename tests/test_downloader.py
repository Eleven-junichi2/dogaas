from src.dogaas.downloader import TaskManager, DownloaderTask


class TestTaskManager:
    @staticmethod
    def test_add_task():
        taskmanager = TaskManager()
        taskmanager.add_task("task_a", DownloaderTask("https://dummy_url_a"))
        assert taskmanager.tasks["task_a"].url == "https://dummy_url_a"

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
