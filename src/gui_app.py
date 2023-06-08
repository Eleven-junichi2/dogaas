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


class DownloaderScene(ft.UserControl):
    def build(self):
        return ft.Text("Hello world")


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
    )
    page.add(tabs)


if __name__ == "__main__":
    ft.app(target=main)
