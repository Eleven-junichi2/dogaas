# TODO: refactoring code

from pathlib import Path
import sys
import json
from typing import Callable

import flet as ft

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


def open_dialog(page: ft.Page, dialog: ft.AlertDialog):
    page.dialog = dialog
    dialog.open = True
    page.update()


def close_dialog(page: ft.Page, dialog: ft.AlertDialog):
    dialog.open = False
    page.update()


task_manager = TaskManager()


class TaskDisplay(ft.UserControl):
    def __init__(
        self,
        task_name: str,
        task_manager: TaskManager,
        delete_task_func: Callable,
    ):
        super().__init__()
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
        remove_btn = ft.Ref[ft.IconButton]()
        self.taskname_display = ft.Ref[ft.TextField]()
        self.url_display = ft.Ref[ft.TextField]()
        self.checkbox = ft.Ref[ft.Checkbox]()
        return ft.Container(
            ft.Row(
                [
                    ft.Checkbox(ref=self.checkbox, value=False),
                    ft.Column(
                        [
                            ft.TextField(
                                ref=self.taskname_display,
                                value=self.task_name,
                                on_submit=lambda e: self.rename_task(),
                            ),
                            ft.TextField(
                                ref=self.url_display,
                                value=self.task_manager.tasks[self.task_name].url,
                                on_submit=lambda e: self.rewrite_task_url(),
                            ),
                        ],
                        expand=1,
                    ),
                    ft.IconButton(
                        ref=remove_btn,
                        icon=ft.icons.DELETE,
                        on_click=lambda e: self.remove_task(),
                    ),
                ],
                expand=1,
            ),
            padding=2,
            border_radius=3,
            border=ft.Border(*[ft.BorderSide(1, ft.colors.TEAL)] * 4),
        )

    def rename_task(self):
        if self.taskname_display.current.value:
            self.task_manager.rename_task(
                self.task_name, self.taskname_display.current.value
            )
            self.taskname_display.current.error_text = None
            self.taskname_display.current.update()
            self.task_name = self.taskname_display.current.value
        else:
            self.taskname_display.current.error_text = i18ntexts["input_dl_task_name"]
            self.taskname_display.current.update()

    def remove_task(self):
        self.task_manager.remove_task(self.task_name)
        self.delete_task_func(self)

    def rewrite_task_url(self):
        if is_url(self.url_display.current.value):
            self.task_manager.tasks[self.task_name].rewrite_url(
                self.url_display.current.value
            )
            self.url_display.current.error_text = None
            self.url_display.current.update()
        else:
            self.url_display.current.error_text = i18ntexts["input_dl_url"]
            self.url_display.current.update()


class DownloaderScene(ft.UserControl):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page = page

    def build(self):
        self.tasks_view = ft.Ref[ft.Column]()
        add_task_btn = ft.Ref[ft.ElevatedButton]()
        self.new_taskname_txtfield = ft.Ref[ft.TextField]()
        self.new_taskurl_txtfield = ft.Ref[ft.TextField]()
        self.download_btn = ft.Ref[ft.ElevatedButton]()
        return ft.Container(
            ft.Column(
                [
                    ft.TextField(
                        ref=self.new_taskname_txtfield,
                        hint_text=i18ntexts["input_dl_task_name"],
                    ),
                    ft.TextField(
                        ref=self.new_taskurl_txtfield,
                        hint_text=i18ntexts["input_dl_url"],
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                ref=add_task_btn,
                                text=i18ntexts["add_task"],
                                icon=ft.icons.ADD,
                                expand=1,
                            )
                        ]
                    ),
                    ft.Column(
                        ref=self.tasks_view,
                        expand=1,
                        spacing=4,
                        scroll=ft.ScrollMode.ALWAYS,
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                ref=self.download_btn,
                                text=i18ntexts["download"],
                                icon=ft.icons.DOWNLOAD,
                                expand=1,
                            )
                        ]
                    ),
                ],
                expand=1,
            ),
            padding=10,
            expand=1,
        )


class SettingsScene(ft.UserControl):
    def build(self):
        return ft.Text("Hello world")


def main(page: ft.Page):
    page.title = "Dogaas"
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(
                text=i18ntexts["tab_header_downloader"], content=DownloaderScene(page)
            ),
            ft.Tab(text=i18ntexts["tab_header_settings"], content=SettingsScene()),
        ],
        expand=1,
    )
    page.add(tabs)


if __name__ == "__main__":
    ft.app(target=main)
