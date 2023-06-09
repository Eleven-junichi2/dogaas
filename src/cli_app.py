from pathlib import Path
import sys
import json

from click_aliases import ClickAliasedGroup
import click
from tqdm import tqdm

from dogaas.downloader import TaskManager, DownloaderTask, DuplicateTaskError, is_url

THIS_SCRIPT_DIR = Path(sys.argv[0]).parent.absolute()
TASKS_FILENAME_WITHOUT_EXT = "tasks"
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
    task_manager.load_tasks_from_json(
        THIS_SCRIPT_DIR / f"{TASKS_FILENAME_WITHOUT_EXT}.json"
    )
except FileNotFoundError:
    pass


@click.group(cls=ClickAliasedGroup)
def cli():
    pass


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
    if is_url(task_url := url):
        task = DownloaderTask(task_url)
    else:
        click.echo(i18ntexts["invalid_url"], err=True)
    try:
        task_manager.add_task(name, task, raise_if_duplicate=True)
    except DuplicateTaskError:
        click.echo(i18ntexts["duplicate_task_name"], err=True)
    else:
        click.secho(i18ntexts["added_task"], fg="bright_green")
        click.secho(i18ntexts["task_name"] + ": " + name, fg="green")
        click.secho("URL: " + task_url, fg="green")
        task_manager.save_tasks_to_json(THIS_SCRIPT_DIR, TASKS_FILENAME_WITHOUT_EXT)


@cli.command(aliases=["rm", "del"], help=i18ntexts["help_msg_remove"])
@click.option(
    "--name",
    "-N",
    prompt=i18ntexts["input_dl_task_name"],
    help=i18ntexts["input_dl_task_name"],
)
def remove(name):
    try:
        task_manager.remove_task(name)
    except KeyError:
        click.echo(i18ntexts["task_for_given_taskname_not_found"], err=True)
    else:
        click.secho(i18ntexts["removed_task"] + ": " + name, fg="bright_green")
        task_manager.save_tasks_to_json(THIS_SCRIPT_DIR, TASKS_FILENAME_WITHOUT_EXT)


@cli.command(aliases=["tasks"], help=i18ntexts["help_msg_remove"])
def list():
    if len(task_manager.tasks) > 0:
        [
            click.echo(f"{i} {task_name} {task.url}")
            for i, (task_name, task) in enumerate(task_manager.tasks.items())
        ]
    else:
        click.echo(i18ntexts["there_are_no_tasks"], err=True)


def validate_dl_taskname(ctx, param, value):
    if isinstance(value, str):
        return value
    else:
        raise click.BadParameter(i18ntexts["there_are_no_tasks"])


@cli.command(aliases=["dl", "do"])
@click.option(
    "--name",
    "-N",
    type=click.Choice(task_manager.tasks.keys()),
    callback=validate_dl_taskname,
    prompt=i18ntexts["input_dl_task_name"],
)
@click.option(
    "--dirpath-for-dest",
    "--dest",
    prompt=i18ntexts["input_destdir_for_dl"],
)
def download(name, dirpath_for_dest):
    print("name: ", name)
    [
        progress_bar
        for progress_bar in tqdm(
            task_manager.download(name, dirpath_for_dest, yield_progress=True)
        )
    ]


if __name__ == "__main__":
    cli()
