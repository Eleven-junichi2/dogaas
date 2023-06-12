from pathlib import Path
import sys
import json

from click_aliases import ClickAliasedGroup
from tqdm import tqdm
import click

from dogaas.downloader import TaskManager, DownloaderTask, DuplicateTaskError, is_url

THIS_SCRIPT_DIR = Path(sys.argv[0]).parent.absolute()
TASKS_FILENAME_WITHOUT_EXT = "tasks"
TASKS_FILE_EXT = "json"
WHERE_TO_SAVE_TASK = THIS_SCRIPT_DIR / f"{TASKS_FILENAME_WITHOUT_EXT}.{TASKS_FILE_EXT}"
CONFIG_FILENAME = "config.json"
I18N_DIRNAME = "i18n"

with open(THIS_SCRIPT_DIR / CONFIG_FILENAME, encoding="utf-8") as f:
    config: dict = json.load(f)

with open(
    THIS_SCRIPT_DIR / I18N_DIRNAME / "cli" / f"{config['language']}.json",
    encoding="utf-8",
) as f:
    i18ntexts: dict[str, str] = json.load(f)

task_manager = TaskManager()

try:
    task_manager.load_tasks_from_json(WHERE_TO_SAVE_TASK)
except FileNotFoundError:
    pass


@click.group(cls=ClickAliasedGroup)
def cli():
    pass


def is_task_exists(msg_if_not_exists=None) -> bool:
    if len(task_manager.tasks) > 0:
        return True
    else:
        if msg_if_not_exists:
            click.echo(msg_if_not_exists, err=True)
        return False


def _tasks():
    click.echo(i18ntexts["where_to_save"] + f": {str(WHERE_TO_SAVE_TASK)}")
    if is_task_exists(msg_if_not_exists=i18ntexts["there_are_no_tasks"]):
        [
            click.echo(f"{i} {task_name} {task.url}")
            for i, (task_name, task) in enumerate(task_manager.tasks.items())
        ]


@cli.command(aliases=["list", "ls", "show"], help=i18ntexts["help_msg_tasks"])
def tasks():
    _tasks()


def _add(name, url):
    if is_url(task_url := url):
        task = DownloaderTask(task_url)
        try:
            task_manager.add_task(name, task, raise_if_duplicate=True)
        except DuplicateTaskError:
            click.echo(i18ntexts["duplicate_task_name"], err=True)
        else:
            click.secho(i18ntexts["added_task"], fg="bright_green")
            click.secho(i18ntexts["task_name"] + ": " + name, fg="green")
            click.secho("URL: " + task_url, fg="green")
            task_manager.save_tasks_to_json(THIS_SCRIPT_DIR, TASKS_FILENAME_WITHOUT_EXT)
    else:
        click.echo(i18ntexts["invalid_url"], err=True)


@cli.command(help=i18ntexts["help_msg_add"])
@click.option(
    "--name",
    "-N",
    prompt=i18ntexts["input_dl_task_name"],
    help=i18ntexts["input_dl_task_name"],
)
@click.option(
    "--url",
    "-L",
    prompt=i18ntexts["input_dl_url"],
    help=i18ntexts["input_dl_url"],
)
def add(name, url):
    _add(name, url)


def _remove(name):
    try:
        task_manager.remove_task(name)
    except KeyError:
        click.echo(i18ntexts["task_for_given_taskname_not_found"], err=True)
    else:
        click.secho(i18ntexts["removed_task"] + ": " + name, fg="bright_green")
        task_manager.save_tasks_to_json(THIS_SCRIPT_DIR, TASKS_FILENAME_WITHOUT_EXT)


@cli.command(aliases=["rm", "del"], help=i18ntexts["help_msg_remove"])
@click.option(
    "--name",
    "-N",
    prompt=i18ntexts["input_dl_task_name"],
    help=i18ntexts["input_dl_task_name"],
)
def remove(name):
    _remove(name)


def _download(name, dirpath_for_dest):
    downloader = task_manager.make_downloader_from_task(name)
    progress_bar = tqdm(
        total=float(downloader.get_filesize_str()),
        unit="iB",
        unit_scale=True,
        mininterval=0,
        miniters=1,
    )
    for progress in downloader.download(dirpath_for_dest, yield_progress=True):
        progress_bar.update(progress)
    progress_bar.close()
    click.secho(i18ntexts["dl_complete"], fg="bright_green")


@cli.command(aliases=["dl", "do"], help=i18ntexts["help_msg_download"])
@click.option(
    "--name",
    "-N",
    type=click.Choice(task_manager.tasks.keys()),
    prompt=i18ntexts["input_dl_task_name"],
)
@click.option(
    "--dirpath-for-dest",
    "--dest",
    prompt=i18ntexts["input_destdir_for_dl"],
    type=click.Path(file_okay=False),
)
def download(name, dirpath_for_dest):
    _download(name, dirpath_for_dest)


@cli.command(help=i18ntexts["help_msg_shell"])
def repl():
    help_text_lines = [
        f"{cmd}\t{cli.commands[cmd].help}"
        for cmd in list(cli.commands.keys())
        if cmd not in ("repl",)
    ]
    help_text_lines.sort()
    [click.echo(help_text) for help_text in help_text_lines]
    while True:
        cmd = click.prompt(i18ntexts["how_to_exit_shell"])
        match cmd:
            # do _command() instead of command() because command() raise an
            # exception when call it in this function.
            case "add":
                name = click.prompt(i18ntexts["input_dl_task_name"])
                url = click.prompt(i18ntexts["input_dl_url"])
                _add(name, url)
            case "remove":
                name = click.prompt(i18ntexts["input_dl_task_name"])
                _remove(name)
            case "tasks":
                _tasks()
            case "download":
                name = click.prompt(
                    i18ntexts["input_dl_task_name"],
                    type=click.Choice(task_manager.tasks.keys()),
                )
                dirpath_for_dest = click.prompt(
                    i18ntexts["input_destdir_for_dl"], type=click.Path(file_okay=False)
                )
                _download(name, dirpath_for_dest)
        if cmd in {"exit", "quit"}:
            sys.exit()


if __name__ == "__main__":
    cli()
