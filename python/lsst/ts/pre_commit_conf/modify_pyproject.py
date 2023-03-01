import pathlib
import shutil

import tomlkit
import tomlkit.toml_file
import typer
from rich.progress import Progress

from .constants import (
    DOT_GITIGNORE,
    FLAKE8_CONFIG_FILE,
    FLAKE8_CONFIG_FILE_NAME,
    ISORT_CONFIG_FILE_NAME,
    ISORT_PRE_COMMIT_HOOK_TEMPLATE,
    ISORT_PYPROJECT_TEMPLATE,
    MYPY_CONFIG_FILE_NAME,
    MYPY_PRE_COMMIT_HOOK_TEMPLATE,
    MYPY_PYPROJECT_TEMPLATE,
    PFLAKE8_PRE_COMMIT_HOOK_TEMPLATE,
    PFLAKE8_PYPROJECT_TEMPLATE,
    PRE_COMMIT_CONFIG_FILE_NAME,
    PRE_COMMIT_CONFIG_TEMPLATE,
)
from .version import __version__

app = typer.Typer()


def version_callback(value: bool) -> None:
    if value:
        print(f"modify_pyproject Version: {__version__}")
        raise typer.Exit()


@app.command()
def modify_pyproject(
    mypy: bool = typer.Option(False, help="Add mypy section to pyproject.toml"),
    dest: pathlib.Path = typer.Argument(".", help="The destination directory."),
    pflake8: bool = typer.Option(
        False,
        help="Add pyproject-flake8 section to pyproject.toml and pre-commit config.",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Return version string of program.",
    ),
) -> None:
    """Modify pyproject.toml for configuration options.
    Add pre-commit config file.
    Copy config files to directory.
    Add files to gitignore.
    """
    with Progress(*Progress.get_default_columns()) as progress:
        task1_total = 2
        if mypy:
            task1_total += 1
        if pflake8:
            task1_total += 1
        task1 = progress.add_task(
            description="Modifying pyproject.toml", total=task1_total
        )
        pyproject_file = dest.resolve() / "pyproject.toml"
        # Add tables to pyproject.toml file.
        with open(pyproject_file) as f:
            doc = tomlkit.load(f)
        with open(ISORT_PYPROJECT_TEMPLATE) as f:
            isort_doc = tomlkit.load(f)
        doc["tool"].update(isort_doc)
        progress.update(task1, advance=1, description="Added isort table.")
        if mypy:
            with open(MYPY_PYPROJECT_TEMPLATE) as f:
                mypy_doc = tomlkit.load(f)
            doc["tool"].update(mypy_doc)
            progress.update(task1, advance=1, description="Added mypy table")
        # pflake8 is for pyproject-flake8 support which adds pyproject
        # support to flake8 via monkey patch.
        if pflake8:
            with open(PFLAKE8_PYPROJECT_TEMPLATE) as f:
                pflake8_doc = tomlkit.load(f)
            doc["tool"].update(pflake8_doc)
            progress.update(task1, advance=1, description="Added flake8 table.")
        doc_file = tomlkit.toml_file.TOMLFile(pyproject_file)
        doc_file.write(doc)
        progress.update(task1, advance=1)
        progress.update(task1, description="pyproject.toml modified.")
        shutil.copy(FLAKE8_CONFIG_FILE, dest)
        with progress.open(
            PRE_COMMIT_CONFIG_TEMPLATE,
            description=f"Reading {PRE_COMMIT_CONFIG_TEMPLATE.name}",
        ) as f:
            pre_commit_config = f.read()
            with progress.open(
                ISORT_PRE_COMMIT_HOOK_TEMPLATE,
                description=f"Reading {ISORT_PRE_COMMIT_HOOK_TEMPLATE.name}",
            ) as f:
                pre_commit_config = pre_commit_config + f.read()
            if mypy:
                with progress.open(
                    MYPY_PRE_COMMIT_HOOK_TEMPLATE,
                    description=f"Reading {MYPY_PRE_COMMIT_HOOK_TEMPLATE.name}",
                ) as f:
                    pre_commit_config = pre_commit_config + f.read()
            if pflake8:
                with progress.open(PFLAKE8_PRE_COMMIT_HOOK_TEMPLATE) as f:
                    pre_commit_config = pre_commit_config + f.read()
            task2 = progress.add_task("Creating pre-commit config file.")
            with open(
                pathlib.Path(dest).resolve() / PRE_COMMIT_CONFIG_FILE_NAME, "w"
            ) as f:
                f.write(pre_commit_config)
            progress.update(
                task2, advance=100, description="pre-commit config written."
            )
        dot_gitignore = dest / DOT_GITIGNORE
        if not dot_gitignore.exists():
            dot_gitignore.touch()

        with progress.open(
            dot_gitignore, description=f"Reading {dot_gitignore.name}"
        ) as f:
            dot_gitignore_contents = f.read()
        with open(dot_gitignore, "a") as f:
            if PRE_COMMIT_CONFIG_FILE_NAME not in dot_gitignore_contents:
                f.write(f"{PRE_COMMIT_CONFIG_FILE_NAME}\n")
            if FLAKE8_CONFIG_FILE_NAME not in dot_gitignore_contents:
                f.write(f"{FLAKE8_CONFIG_FILE_NAME}\n")
            if ISORT_CONFIG_FILE_NAME not in dot_gitignore_contents:
                f.write(f"{ISORT_CONFIG_FILE_NAME}\n")
            if (mypy) and MYPY_CONFIG_FILE_NAME not in dot_gitignore_contents:
                f.write(f"{MYPY_CONFIG_FILE_NAME}\n")
