from pathlib import Path
import sys
import json
from typing import Callable

import flet as ft
import requests

from dogaas.downloader import TaskManager, DownloaderTask, is_url

THIS_SCRIPT_DIR = Path(sys.argv[0]).parent.absolute()
CONFIG_FILENAME = "config.json"
I18N_DIRNAME = "i18n"

with open(THIS_SCRIPT_DIR / CONFIG_FILENAME, encoding="utf-8") as f:
    config: dict = json.load(f)

with open(
    THIS_SCRIPT_DIR / I18N_DIRNAME / "gui" / f"{config['language']}.json",
    encoding="utf-8",
) as f:
    i18ntexts: dict[str, str] = json.load(f)


class TaskDisplay(ft.UserControl):
    def __init__(
        self,
        downloader_task: DownloaderTask,
        task_name: str,
        task_manager: TaskManager,
        delete_task_func: Callable,
    ):
        super().__init__()
        if isinstance(downloader_task, DownloaderTask):
            self.task = downloader_task
        else:
            raise TypeError("`downloader_task` must be `DownloaderTask`")
        if isinstance(task_name, str):
            self.task_name = task_name
        else:
            raise TypeError("`task_name` must be `str`")
        if isinstance(task_manager, TaskManager):
            self.task_manager = task_manager
        else:
            raise TypeError("`task_manager` must be `TaskManager`")
        self.delete_task_func = delete_task_func

    def build(self):
        remove_btn = ft.IconButton(
            ft.icons.DELETE, on_click=lambda e: self.remove_task()
        )
        self.task_name_display = ft.TextField(
            value=self.task_name, on_submit=lambda e: self.rename_task()
        )
        self.url_display = ft.TextField(
            value=self.task.url, on_submit=lambda e: self.rewrite_task_url()
        )
        self.checkbox = ft.Checkbox(value=False)
        return ft.Container(
            ft.Row(
                [
                    self.checkbox,
                    ft.Column([self.task_name_display, self.url_display], expand=1),
                    remove_btn,
                ],
                expand=1,
            ),
            padding=2,
            border_radius=3,
            border=ft.Border(*[ft.BorderSide(1, ft.colors.TEAL)] * 4),
        )

    def rename_task(self):
        if self.task_name_display.value:
            self.task_manager.rename_task(self.task_name, self.task_name_display.value)
            self.task_name_display.error_text = None
            self.task_name_display.update()

        else:
            self.task_name_display.error_text = i18ntexts["input_dl_task_name"]
            self.task_name_display.update()

    def remove_task(self):
        self.task_manager.remove_task(self.task_name)
        self.delete_task_func(self)

    def rewrite_task_url(self):
        if is_url(self.url_display.value):
            self.task_manager.tasks[self.task_name].rewrite_url(self.url_display.value)
            self.task_name_display.error_text = None
            self.task_name_display.update()
        else:
            self.task_name_display.error_text = i18ntexts["input_dl_url"]
            self.task_name_display.update()


class DownloaderScene(ft.UserControl):
    def build(self):
        self.dltask_manager = TaskManager()
        self.tasks_view = ft.Column(expand=1, spacing=4, scroll=ft.ScrollMode.ALWAYS)
        add_task_btn = ft.ElevatedButton(
            text=i18ntexts["add_task"],
            icon=ft.icons.ADD,
            expand=1,
            on_click=lambda e: self.add_task(),
        )
        self.new_task_name_textfield = ft.TextField(
            hint_text=i18ntexts["input_dl_task_name"],
        )
        self.new_task_url_textfield = ft.TextField(hint_text=i18ntexts["input_dl_url"])
        return ft.Container(
            ft.Column(
                [
                    self.new_task_name_textfield,
                    self.new_task_url_textfield,
                    ft.Row([add_task_btn]),
                    self.tasks_view,
                ],
                expand=1,
            ),
            padding=10,
            expand=1,
        )

    def do_downloader_tasks(self):
        # TODO: open filedialog to get where to save downloads
        urls = []
        successful_task_names = []
        for task in self.dltask_manager:
            pass

    def add_task(self):
        invalid_task = False
        if not (task_name := self.new_task_name_textfield.value):
            self.new_task_name_textfield.error_text = i18ntexts["input_dl_task_name"]
            self.new_task_name_textfield.update()
            invalid_task = True
        elif self.dltask_manager.tasks.get(task_name):
            self.new_task_name_textfield.error_text = i18ntexts["duplicate_task_name"]
            self.new_task_name_textfield.update()
            invalid_task = True
        if not is_url(task_url := self.new_task_url_textfield.value):
            self.new_task_url_textfield.error_text = i18ntexts["input_dl_url"]
            self.new_task_url_textfield.update()
            invalid_task = True
        if invalid_task:
            return
        else:
            new_task = DownloaderTask(task_url)
            self.dltask_manager.add_task(name=task_name, task=new_task)
            self._add_taskdisplay(
                TaskDisplay(
                    new_task,
                    task_name=task_name,
                    task_manager=self.dltask_manager,
                    delete_task_func=self._delete_task,
                )
            )
            self.new_task_name_textfield.error_text = None
            self.new_task_name_textfield.update()
            self.new_task_url_textfield.error_text = None
            self.new_task_url_textfield.update()

    def _add_taskdisplay(self, taskdisplay: TaskDisplay):
        if isinstance(taskdisplay, TaskDisplay):
            self.tasks_view.controls.append(taskdisplay)
            self.tasks_view.update()
        else:
            raise TypeError("`taskdisplay` must be `TaskDisplay`")

    def _delete_task(self, taskdisplay: TaskDisplay):
        if isinstance(taskdisplay, TaskDisplay):
            self.tasks_view.controls.remove(taskdisplay)
            self.tasks_view.update()


class SettingsScene(ft.UserControl):
    def build(self):
        return ft.Text("Hello world")


def main(page: ft.Page):
    page.title = "Dogaas"
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(text=i18ntexts["tab_header_downloader"], content=DownloaderScene()),
            ft.Tab(text=i18ntexts["tab_header_settings"], content=SettingsScene()),
        ],
        expand=1,
    )
    page.add(tabs)


if __name__ == "__main__":
    ft.app(target=main)
