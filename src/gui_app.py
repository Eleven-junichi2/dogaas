from pathlib import Path
import sys
import json

import flet as ft

from dogaas.downloader import Downloader

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

downloader = Downloader()


class TasksView(ft.UserControl):
    def build(self):
        tasks_view = ft.ListView(expand=1)
        return tasks_view


class TaskDisplay(ft.UserControl):
    def __init__(self, task_name: str):
        self.task_name = task_name

    def build(self):
        remove_btn = ft.IconButton(ft.icons.DELETE)
        url_display = ft.TextField(value=self.task_name)
        return ft.Row([url_display, remove_btn])


class DownloaderScene(ft.UserControl):
    def build(self):
        add_task_btn = ft.ElevatedButton(
            text=i18ntexts["add_task"],
            icon=ft.icons.ADD,
            expand=1
        )
        new_task_name_textfield = ft.TextField()
        new_task_url_textfield = ft.TextField()
        tasks_view = TasksView()
        return ft.Container(
            ft.Column(
                [
                    new_task_name_textfield,
                    new_task_url_textfield,
                    ft.Row([add_task_btn]),
                    tasks_view
                ]
            ),
            padding=10,
        )


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
