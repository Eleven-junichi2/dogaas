# TODO: refactor code

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
        self.dltask_manager = TaskManager()
        self.dirdialog = ft.FilePicker(
            on_result=lambda e: self.set_dirpath_for_dest_of_dl(e)
        )
        self.page.overlay.append(self.dirdialog)

        def open_dirdialog_after_close_confirm_dl_dialog(dialog: ft.AlertDialog):
            close_dialog(self.page, dialog)
            self.dirdialog.get_directory_path(initial_directory=THIS_SCRIPT_DIR)

        self.confirm_dl_dialog = ft.AlertDialog(
            title=ft.Text(i18ntexts["ask_confirm_dl"]),
            actions=[
                ft.TextButton(
                    text=i18ntexts["yes"],
                    on_click=lambda e: open_dirdialog_after_close_confirm_dl_dialog(
                        self.confirm_dl_dialog
                    ),
                ),
                ft.TextButton(
                    text=i18ntexts["no"],
                    on_click=lambda e: close_dialog(self.page, self.confirm_dl_dialog),
                ),
            ],
        )
        self.dl_progress_bar = ft.ProgressBar(
            expand=1, color=ft.colors.AMBER, bgcolor="#ddddee"
        )
        self.show_dl_progress_dialog = ft.AlertDialog(
            title=ft.Text(i18ntexts["doing_download"]),
            content=self.dl_progress_bar,
            modal=True,
        )

    def set_dirpath_for_dest_of_dl(self, e: ft.FilePickerResultEvent):
        self.dirpath_for_dest_of_downloads = e.path
        self.do_downloader_tasks()

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
                                on_click=lambda e: self.add_task(),
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
                                on_click=lambda e: self.open_dialog_to_confirm_dl(
                                    self.confirm_dl_dialog
                                ),
                            )
                        ]
                    ),
                ],
                expand=1,
            ),
            padding=10,
            expand=1,
        )

    def get_listview_for_reserved_tasks(self) -> ft.Column:
        listview = ft.Column(
            [ft.Text(task_name) for task_name in self.reserved_tasknames()],
            scroll=ft.ScrollMode.ALWAYS,
            expand=1,
        )
        return listview

    def open_dialog_to_confirm_dl(self, dialog: ft.AlertDialog):
        reserved_task_names = self.get_listview_for_reserved_tasks()
        if self.dltask_manager.tasks and len(reserved_task_names.controls) > 0:
            dialog.content = reserved_task_names
            open_dialog(self.page, dialog)
        else:
            if not self.new_taskname_txtfield.current.value:
                self.show_err_for_newtaskname_textfield(i18ntexts["input_dl_task_name"])
            if not is_url(self.new_taskurl_txtfield.current.value):
                self.show_err_for_newtaskurl_textfield(i18ntexts["input_dl_url"])

    def reserved_tasknames(self) -> list[str]:
        print(self.tasks_view.current.controls)
        return [
            taskdisplay.task_name
            for taskdisplay in self.tasks_view.current.controls
            if taskdisplay.checkbox.current.value
        ]

    def do_downloader_tasks(self):
        # TODO: open filedialog to get where to save downloads
        def close_all_dialog():
            close_dialog(self.page, self.show_dl_progress_dialog)

        open_dialog(self.page, self.show_dl_progress_dialog)
        dirpath_for_dest_of_downloads = self.dirpath_for_dest_of_downloads
        for task_name, reserved_task_name in zip(
            self.dltask_manager.tasks.keys(), self.reserved_tasknames()
        ):
            if task_name == reserved_task_name:
                for progress in self.dltask_manager.download(
                    task_name, dirpath_for_dest_of_downloads
                ):
                    self.dl_progress_bar.value = progress
                    self.show_dl_progress_dialog.title.text = (
                        i18ntexts["doing_download"] + ": " + task_name
                    )
        self.show_dl_progress_dialog.title.text = i18ntexts["dl_complete"]
        self.show_dl_progress_dialog.modal = False
        self.show_dl_progress_dialog.actions = [
            ft.ElevatedButton(
                text=i18ntexts["close"],
                icon=ft.icons.CLOSE,
                on_click=lambda e: close_all_dialog(),
            )
        ]
        self.show_dl_progress_dialog.update()
        self.dl_progress_bar.color = ft.colors.GREEN_ACCENT
        self.dl_progress_bar.update()

    def show_err_for_newtaskname_textfield(self, err_text: str):
        self.new_taskname_txtfield.current.error_text = err_text
        self.new_taskname_txtfield.current.update()

    def show_err_for_newtaskurl_textfield(self, err_text: str):
        self.new_taskurl_txtfield.current.error_text = err_text
        self.new_taskurl_txtfield.current.update()

    def clear_err_txt_of_newtaskurl_textfield(self):
        self.new_taskurl_txtfield.current.error_text = None
        self.new_taskurl_txtfield.current.update()

    def clear_err_txt_of_newtaskname_textfield(self):
        self.new_taskname_txtfield.current.error_text = None
        self.new_taskname_txtfield.current.update()

    def add_task(self):
        invalid_task = False
        if not (task_name := self.new_taskname_txtfield.current.value):
            self.show_err_for_newtaskname_textfield(i18ntexts["input_dl_task_name"])
            invalid_task = True
        elif self.dltask_manager.tasks.get(task_name):
            self.show_err_for_newtaskname_textfield(i18ntexts["duplicate_task_name"])
            invalid_task = True
        if not is_url(task_url := self.new_taskurl_txtfield.current.value):
            self.show_err_for_newtaskurl_textfield(i18ntexts["input_dl_url"])
            invalid_task = True
        if not invalid_task:
            self.dltask_manager.add_task(name=task_name, task=DownloaderTask(task_url))
            self.tasks_view.current.controls.append(
                TaskDisplay(
                    task_name=task_name,
                    task_manager=self.dltask_manager,
                    delete_task_func=self._delete_task,
                )
            )
            self.tasks_view.current.update()
            self.clear_err_txt_of_newtaskname_textfield()
            self.clear_err_txt_of_newtaskurl_textfield()

    def _delete_task(self, taskdisplay: TaskDisplay):
        if isinstance(taskdisplay, TaskDisplay):
            self.tasks_view.current.controls.remove(taskdisplay)
            self.tasks_view.current.update()


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
