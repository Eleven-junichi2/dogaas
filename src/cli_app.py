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


ALIASES_FOR_SHELL_SUBCMD = ["interact", "interactive-shell", "interactive"]


@cli.command(
    aliases=ALIASES_FOR_SHELL_SUBCMD,
    help=i18ntexts["help_msg_shell"],
)
def shell():
    while True:
        args_str: str = click.prompt(
            "", prompt_suffix=f"{i18ntexts['how_to_exit_shell']}> "
        )
        # -prevent to shell called-
        if (args := args_str.split(" "))[0] not in ALIASES_FOR_SHELL_SUBCMD + ["shell"]:
            break
        # --
    try:
        cli.main(args=args)
    except SystemExit:
        pass
    click.pause(i18ntexts["pause_input_to_end"])


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
    type=click.Path(file_okay=False),
)
def download(name, dirpath_for_dest):
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


if __name__ == "__main__":
    cli()
