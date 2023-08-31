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

import yaml

__all__ = [
    "DOT_GITIGNORE",
    "CLANG_FORMAT_CONFIG_FILE_NAME",
    "CLANG_FORMAT_CONFIG_FILE",
    "FLAKE8_CONFIG_FILE",
    "FLAKE8_CONFIG_FILE_NAME",
    "ISORT_CONFIG_FILE",
    "ISORT_CONFIG_FILE_NAME",
    "MYPY_CONFIG_FILE",
    "MYPY_CONFIG_FILE_NAME",
    "PRE_COMMIT_CONFIG_FILE_NAME",
    "TS_PRE_COMMIT_CONFIG_YAML",
    "copy_config_files",
    "create_or_report_missing_config_file",
    "generate_pre_commit_conf",
    "generate_pre_commit_conf_file",
    "parse_args",
    "update_args_from_config_file",
    "update_dot_gitignore",
    "validate_config_file_contents",
]

# The root of the current file to be used by the Path definitions below.
ROOT = pathlib.Path(__file__)

# The YAML file holding the configuration for the "generate_pre_commit_conf"
# command.
TS_PRE_COMMIT_CONFIG_YAML = ".ts_pre_commit_config.yaml"

# Directories with data used by this script.
CONFIG_FILES_DIR = ROOT.resolve().parents[0] / "config_files"
TEMPLATES_DIR = ROOT.resolve().parents[0] / "templates"

# Config files for the pre-commit hooks.
CLANG_FORMAT_CONFIG_FILE_NAME = ".clang-format"
FLAKE8_CONFIG_FILE_NAME = ".flake8"
ISORT_CONFIG_FILE_NAME = ".isort.cfg"
MYPY_CONFIG_FILE_NAME = ".mypy.ini"
PRE_COMMIT_CONFIG_FILE_NAME = ".pre-commit-config.yaml"

# Config file paths for the pre-commit hooks.
CLANG_FORMAT_CONFIG_FILE = CONFIG_FILES_DIR / CLANG_FORMAT_CONFIG_FILE_NAME
TS_PRE_COMMIT_CONFIG_YAML_FILE = CONFIG_FILES_DIR / TS_PRE_COMMIT_CONFIG_YAML
FLAKE8_CONFIG_FILE = CONFIG_FILES_DIR / FLAKE8_CONFIG_FILE_NAME
ISORT_CONFIG_FILE = CONFIG_FILES_DIR / ISORT_CONFIG_FILE_NAME
MYPY_CONFIG_FILE = CONFIG_FILES_DIR / MYPY_CONFIG_FILE_NAME

# Template files.
MYPY_PRE_COMMIT_HOOK_TEMPLATE = TEMPLATES_DIR / "mypy-pre-commit-hook-template.yaml"
PRE_COMMIT_CONFIG_TEMPLATE = TEMPLATES_DIR / "pre-commit-config-template.yaml"

DOT_GITIGNORE = ".gitignore"

# Mandatory pre-commit hooks for TSSW.
MANDATORY_PRE_COMMIT_HOOKS = frozenset(
    ("check-yaml", "check-xml", "black", "flake8", "isort")
)

# Optional pre-commit hooks for TSSW and the arg used for them. If arg is None,
# there isn't argument to turn those off.
OPTIONAL_PRE_COMMIT_HOOKS = {"mypy": "no_mypy", "clang-format": None}

# All pre-commit hooks for TSSW.
ALL_PRE_COMMIT_HOOKS = MANDATORY_PRE_COMMIT_HOOKS.union(OPTIONAL_PRE_COMMIT_HOOKS)


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
        "--no-mypy",
        action="store_true",
        default=False,
        help="Generate a pre-commit configuration file without mypy "
        "(default: False, meaning mypy gets included). This options requires "
        "--create to be specified as well.",
    )

    parser.add_argument(
        "--create",
        action="store_true",
        default=False,
        help="Create a .ts_pre_commit_conf.yaml configuration file "
        "(default: False, meaning no configuration file is created).",
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
    if sn.no_mypy is True and sn.create is False:
        raise ValueError("Specifying --no-mypy requires --create as well.")

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


def create_or_report_missing_config_file(args: types.SimpleNamespace) -> None:
    """Verify that the .ts_pre_commit_config.yaml config file exists and either
    create one or report that it is missing, depending on the provided args.

    Parameters
    ----------
    args : `types.SimpleNamespace`
        The args that determine the destination path and whether a config file
        should be created if it is missing.

    Raises
    ------
    FileNotFoundError
        In case the config file doesn't exist and will not be created. The
        error message contains the instructions for how to create the missing
        config file.
    """
    dest = _get_dest(args=args)
    config_path = dest / TS_PRE_COMMIT_CONFIG_YAML
    if not config_path.exists():
        print(f"No config file {TS_PRE_COMMIT_CONFIG_YAML} found.", end=" ")
        if args.create is True:
            _create_config_file(args)
        else:
            _print_instructions_and_exit(args)
    elif args.create is True:
        print(
            f"Config file {TS_PRE_COMMIT_CONFIG_YAML_FILE} already exists, no action performed."
        )
        sys.exit(1)


def _create_config_file(args: types.SimpleNamespace) -> None:
    """Create a .ts_pre_commit_config.yaml config file with contents based on
    the provided arguments.

    Parameters
    ----------
    args : `types.SimpleNamespace`
        The args that determine the destination path and contents of the config
        file.
    """
    dest = _get_dest(args=args)
    print("Creating one now.")
    shutil.copy(TS_PRE_COMMIT_CONFIG_YAML_FILE, dest)

    with open(dest / TS_PRE_COMMIT_CONFIG_YAML, "r") as f:
        lines = f.read()

    if args.no_mypy is True:
        lines = lines.replace("mypy: true", "mypy: false")

    with open(dest / TS_PRE_COMMIT_CONFIG_YAML, "w") as f:
        f.write(lines)


def _print_instructions_and_exit(args: types.SimpleNamespace) -> None:
    """Print instructions for how to create a .ts_pre_commit_config.yaml config
    file and exit.

    Parameters
    ----------
    args : `types.SimpleNamespace`
        The args that determine the destination path and contents of the config
        file.

    Raises
    ------
    FileNotFoundError
        The error message contains the instructions for how to create the
        missing config file.
    """
    message = "Create one by copying and pasting the following lines:\n"
    message += "\n"
    message += "check-yaml: true\n"
    message += "check-xml: true\n"
    message += "clang-format: true\n"
    message += "black: true\n"
    message += "flake8: true\n"
    message += "isort: true\n"
    message += f"mypy: {'true' if args.no_mypy is False else 'false'}\n"
    raise FileNotFoundError(message)


def validate_config_file_contents(args: types.SimpleNamespace) -> None:
    """Validate the contents of the .ts_pre_commit_config.yaml config file. The
    following pre-commit hooks need to be present in the config file:

        check-yaml
        check-xml
        clang-format
        black
        flake8
        isort
        mypy

    All pre-commit hooks are mandatory, so all need to be set to "yes", with
    the exception of mypy, which may be set to "no". No additional pre-commit
    hooks may be defined.

    Parameters
    ----------
    args : `types.SimpleNamespace`
        The args that determine the path to the config file.

    Raises
    ------
    ValueError
        In case of incorrect, missing or not allowed pre-commit hook config
        options.

    Notes
    -----
    The script will fail with a comprehensive error message if any of the
    pre-commit hooks used by TSSW are missing, if any of the mandatory
    pre-commit hooks are set to "no" or if any additional pre-commit hooks
    (meaning any non-empty line that is not a comment) is present.
    """
    dest = _get_dest(args=args)
    with open(dest / TS_PRE_COMMIT_CONFIG_YAML) as f:
        config = yaml.safe_load(f)

    missing_hooks = []
    incorrect_config_options = []
    additional_hooks = []
    for hook in ALL_PRE_COMMIT_HOOKS:
        missing = True
        for option in config:
            if option == hook:
                missing = False
                break
        if (
            hook in OPTIONAL_PRE_COMMIT_HOOKS.keys()
            and OPTIONAL_PRE_COMMIT_HOOKS[hook] is None
        ):
            missing = False
            break
        if missing:
            missing_hooks.append(hook)
    for hook in MANDATORY_PRE_COMMIT_HOOKS:
        incorrect_config_option = True
        for option in config:
            if option == hook and config[option] is True:
                incorrect_config_option = False
                break
        if incorrect_config_option:
            incorrect_config_options.append(hook)
    for option in config:
        additional_hook = True
        for hook in ALL_PRE_COMMIT_HOOKS:
            if option == hook:
                additional_hook = False
                continue
        if additional_hook:
            additional_hooks.append(option)

    exit_messages = []
    if missing_hooks:
        exit_messages.append(
            f"The following pre-commit hooks are missing: {sorted(missing_hooks)}"
        )
    if incorrect_config_options:
        exit_messages.append(
            "The following mandatory pre-commit hooks are "
            + f"not set to 'true': {sorted(incorrect_config_options)}"
        )
    if additional_hooks:
        exit_messages.append(
            f"Please remove the following additional lines: {additional_hooks}"
        )

    if missing_hooks or incorrect_config_options or additional_hooks:
        raise ValueError("\n".join(exit_messages))


def update_args_from_config_file(args: types.SimpleNamespace) -> None:
    """Read the .ts_pre_commit_config.yaml config file and update the args
    accordingly.

    Parameters
    ----------
    args : `types.SimpleNamespace`
        The args that determine the destination path and the contents of the
        config file.
    """
    dest = _get_dest(args=args)
    with open(dest / TS_PRE_COMMIT_CONFIG_YAML) as f:
        config = yaml.safe_load(f)

    for hook in OPTIONAL_PRE_COMMIT_HOOKS:
        arg = OPTIONAL_PRE_COMMIT_HOOKS[hook]
        if arg is not None:
            option = config[hook]
            setattr(args, arg, not option)


def generate_pre_commit_conf_file(args: types.SimpleNamespace) -> None:
    """Generate the '.pre-commit-config.yaml' file. Both the contents and the
    destination path are determined from the provided args.

    Parameters
    ----------
    args : `types.SimpleNamespace`
        The args that determine the contents and the destination path.
    """
    dest = _get_dest(args=args)
    with open(PRE_COMMIT_CONFIG_TEMPLATE) as f:
        pre_commit_config = f.read()
    if args.no_mypy is False:
        with open(MYPY_PRE_COMMIT_HOOK_TEMPLATE) as f:
            pre_commit_config += f.read()
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
    shutil.copy(CLANG_FORMAT_CONFIG_FILE, dest)
    shutil.copy(FLAKE8_CONFIG_FILE, dest)
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
        if CLANG_FORMAT_CONFIG_FILE_NAME not in dot_gitignore_contents:
            f.write(f"{CLANG_FORMAT_CONFIG_FILE_NAME}\n")
        if FLAKE8_CONFIG_FILE_NAME not in dot_gitignore_contents:
            f.write(f"{FLAKE8_CONFIG_FILE_NAME}\n")
        if ISORT_CONFIG_FILE_NAME not in dot_gitignore_contents:
            f.write(f"{ISORT_CONFIG_FILE_NAME}\n")
        if MYPY_CONFIG_FILE_NAME not in dot_gitignore_contents:
            f.write(f"{MYPY_CONFIG_FILE_NAME}\n")


def generate_pre_commit_conf() -> None:
    """Main function that generates the .prec-ommit-config.yaml file. It also
    copies the required pre-commit hook config files and updates/creates the
    .gitignore file.
    """
    command_line_args = sys.argv[1:]
    try:
        args = parse_args(command_line_args=command_line_args)
        create_or_report_missing_config_file(args)
        validate_config_file_contents(args)
    except (ValueError, FileNotFoundError) as e:
        sys.exit(str(e))
    update_args_from_config_file(args)
    generate_pre_commit_conf_file(args)
    copy_config_files(args)
    update_dot_gitignore(args)
