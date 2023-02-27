# This file is part of ts_pre_commit_conf.
#
# Developed for the Vera Rubin Observatory Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
import pathlib
import shutil
import sys
import types

from .constants import (
    DOT_GITIGNORE,
    FLAKE8_CONFIG_FILE,
    FLAKE8_CONFIG_FILE_NAME,
    ISORT_CONFIG_FILE,
    ISORT_CONFIG_FILE_NAME,
    ISORT_PRE_COMMIT_HOOK_TEMPLATE,
    MYPY_CONFIG_FILE,
    MYPY_CONFIG_FILE_NAME,
    MYPY_PRE_COMMIT_HOOK_TEMPLATE,
    PRE_COMMIT_CONFIG_FILE_NAME,
    PRE_COMMIT_CONFIG_TEMPLATE,
)

__all__ = [
    "copy_config_files",
    "generate_pre_commit_conf",
    "generate_pre_commit_conf_file",
    "parse_args",
    "update_dot_gitignore",
]


def parse_args(command_line_args: list[str]) -> types.SimpleNamespace:
    """Parse the command line arguments provided when calling this script.

    Parameters
    ----------
    command_line_args : `list` of `str`
        The command line arguments as provided when calling this script.

    Returns
    -------
    `types.SimpleNamespace`
        The parsed command line arguments.
    """
    parser = argparse.ArgumentParser(
        prog="generate_pre_commit_conf",
        description="This script generates the config files for pre-commit and its hooks.",
        epilog="This script doesn't delete existing configuration files so you need to remove "
        "those manually if necessary.",
    )

    parser.add_argument(
        "--no-isort",
        action="store_true",
        default=False,
        help="Generate a pre-commit configuration file without isort "
        "(default: False, meaning isort gets included).",
    )

    parser.add_argument(
        "--no-mypy",
        action="store_true",
        default=False,
        help="Generate a pre-commit configuration file without mypy "
        "(default: False, meaning mypy gets included).",
    )

    parser.add_argument(
        "--dest",
        default=".",
        help="The destination folder to install the pre-commit configurations files into "
        "(default: '.' meaning the current working directory). Intended to be used by "
        "scripts that update more than one project at a time.",
    )

    args = parser.parse_args(command_line_args)
    sn = types.SimpleNamespace()
    for var in vars(args):
        setattr(sn, var, getattr(args, var))
    return sn


def _get_dest(args: types.SimpleNamespace) -> pathlib.Path:
    """Get the value of 'dest' from the provided args, or return the default
    value '.' if not present.

    Parameters
    ----------
    args : `types.SimpleNamespace`
        The args that may contain

    Returns
    -------
    `pathlib.Path`
        The value of 'dest' or of the default value as a Path.
    """
    dest = pathlib.Path(".")
    if "dest" in vars(args):
        dest = pathlib.Path(args.dest)
    return dest


def generate_pre_commit_conf_file(args: types.SimpleNamespace) -> None:
    """Generate the '.pre-commit-conif.yaml' file. Both the contents and the
    destination path are determined from the provided args.

    Parameters
    ----------
    args : `types.SimpleNamespace`
        The args that determine the contents and the destination path.
    """
    dest = _get_dest(args=args)
    with open(PRE_COMMIT_CONFIG_TEMPLATE) as f:
        pre_commit_config = f.read()
    if "no_isort" not in vars(args) or args.no_isort is False:
        with open(ISORT_PRE_COMMIT_HOOK_TEMPLATE) as f:
            pre_commit_config = pre_commit_config + f.read()
    if "no_mypy" not in vars(args) or args.no_mypy is False:
        with open(MYPY_PRE_COMMIT_HOOK_TEMPLATE) as f:
            pre_commit_config = pre_commit_config + f.read()
    with open(pathlib.Path(dest) / PRE_COMMIT_CONFIG_FILE_NAME, "w") as f:
        f.write(pre_commit_config)


def copy_config_files(args: types.SimpleNamespace) -> None:
    """Copy the pre-hook config files. The provided args are used to determine
    which files to copy and which destination path to copy them to.

    Parameters
    ----------
    args : `types.SimpleNamespace`
        The args that determine which files get copied and which destination
        path to copy them to.
    """
    dest = _get_dest(args=args)
    shutil.copy(FLAKE8_CONFIG_FILE, dest)
    if "no_isort" not in vars(args) or args.no_isort is False:
        shutil.copy(ISORT_CONFIG_FILE, dest)
    if "no_mypy" not in vars(args) or args.no_mypy is False:
        shutil.copy(MYPY_CONFIG_FILE, dest)


def update_dot_gitignore(args: types.SimpleNamespace) -> None:
    """Update the .gitignore file to contain entries for the pre-hook config
    files. The provided args are used to determine which file names to add
    and which destination path the .gitignore file is expected to be in. If no
    .gitignore file is found at the destination path, it is created.

    Parameters
    ----------
    args : `types.SimpleNamespace`
        The args that determine which file names to add and which destination
        path the .gitignore file is expected to be in.
    """
    dest = _get_dest(args=args)
    dot_gitignore = dest / DOT_GITIGNORE
    if not dot_gitignore.exists():
        dot_gitignore.touch()

    with open(dot_gitignore) as f:
        dot_gitignore_contents = f.read()
    with open(dot_gitignore, "a") as f:
        if PRE_COMMIT_CONFIG_FILE_NAME not in dot_gitignore_contents:
            f.write(f"{PRE_COMMIT_CONFIG_FILE_NAME}\n")
        if FLAKE8_CONFIG_FILE_NAME not in dot_gitignore_contents:
            f.write(f"{FLAKE8_CONFIG_FILE_NAME}\n")
        if (
            "no_isort" not in vars(args) or args.no_isort is False
        ) and ISORT_CONFIG_FILE_NAME not in dot_gitignore_contents:
            f.write(f"{ISORT_CONFIG_FILE_NAME}\n")
        if (
            "no_mypy" not in vars(args) or args.no_mypy is False
        ) and MYPY_CONFIG_FILE_NAME not in dot_gitignore_contents:
            f.write(f"{MYPY_CONFIG_FILE_NAME}\n")


def generate_pre_commit_conf() -> None:
    """Main function that generates the .prec-ommit-config.yaml file. It also
    copies the required pre-commit hook config files and updates/creates the
    .gitignore file.
    """
    command_line_args = sys.argv[1:]
    args = parse_args(command_line_args=command_line_args)
    generate_pre_commit_conf_file(args)
    copy_config_files(args)
    update_dot_gitignore(args)
