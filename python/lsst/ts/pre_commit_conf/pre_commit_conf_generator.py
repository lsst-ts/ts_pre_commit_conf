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

__all__ = [
    "DOT_GITIGNORE",
    "PRE_COMMIT_CONFIG_FILE_NAME",
    "TS_PRE_COMMIT_CONFIG_YAML",
    "create_config_files",
    "create_or_report_missing_config_file",
    "generate_pre_commit_conf",
    "generate_pre_commit_conf_file",
    "parse_args",
    "run_pre_commit_install",
    "update_args_from_config_file",
    "update_dot_gitignore",
    "validate_config_file_contents",
]

import argparse
import asyncio
import os
import pathlib
import shutil
import sys
import types

import yaml

from .pre_commit_hooks import PreCommitHookMetadata, RuleType, registry

# The YAML file holding the configuration for the "generate_pre_commit_conf"
# command.
TS_PRE_COMMIT_CONFIG_YAML = ".ts_pre_commit_config.yaml"

# The YAML file holding the configurations for the pre-commit hooks.
PRE_COMMIT_CONFIG_FILE_NAME = ".pre-commit-config.yaml"

# The Git ignore file.
DOT_GITIGNORE = ".gitignore"

# Process timeout (sec)
PROCESS_TIMEOUT = 5


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
        "--create",
        action="store_true",
        default=False,
        help="Create a .ts_pre_commit_conf.yaml configuration file "
        "(default: False, meaning no configuration file is created).",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing hook configuration files "
        "(default: False, meaning exisitng files are not overwritten).",
    )

    parser.add_argument(
        "--dest",
        default=".",
        help="The destination folder to install the pre-commit configurations files into "
        "(default: '.' meaning the current working directory). Intended to be used by "
        "scripts that update more than one project at a time.",
    )

    parser.add_argument(
        "--skip-pre-commit-install",
        default=False,
        action="store_true",
        help="Skip running 'pre-commit install'. This should only be done on Jenkins.",
    )

    for hook_name in registry:
        hook = registry[hook_name]
        if hook.rule_type == RuleType.OPT_OUT:
            parser.add_argument(
                f"--no-{hook_name}",
                action="store_true",
                default=False,
                help=f"Exclude {hook_name} from the pre-commit configuration. "
                f"(default: False, meaning {hook_name} gets included). This options requires "
                "--create to be specified as well.",
            )
        elif hook.rule_type == RuleType.OPT_IN:
            parser.add_argument(
                f"--with-{hook_name}",
                action="store_true",
                default=False,
                help=f"Include {hook_name} in the pre-commit configuration. "
                f"(default: False, meaning {hook_name} is not included). This options requires "
                "--create to be specified as well.",
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
    print("Creating config file.")
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
            f"Config file {TS_PRE_COMMIT_CONFIG_YAML} already exists, no action performed."
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
    lines: list[str] = []
    for hook_name in registry:
        if hook_name == "pre-commit-hooks":
            # These hooks are always part of TS_PRE_COMMIT_CONFIG_YAML.
            lines.append("check-yaml: true")
            lines.append("check-xml: true")
            continue
        hook = registry[hook_name]
        if hook.rule_type == RuleType.MANDATORY:
            lines.append(f"{hook_name}: true")
        else:
            # If the rule is opt-out, the arg name prefix is "no"; if the rule
            # is opt-in it is "with".
            hook_arg_name_prefix = (
                "no" if hook.rule_type == RuleType.OPT_OUT else "with"
            )
            arg = getattr(
                args,
                f"{hook_arg_name_prefix}_{hook_name.replace('-', '_')}",
                hook.rule_type == RuleType.OPT_IN,
            )
            # need to flip the boolean if this rule is opt_in.
            if hook.rule_type == RuleType.OPT_IN:
                arg = not arg
            lines.append(f"{hook_name}: {'true' if arg is False else 'false'}")
    lines = sorted(lines)
    _write_ts_pre_commit_config_yaml(dest, lines)


def _write_ts_pre_commit_config_yaml(dest: pathlib.Path, lines: list[str]) -> None:
    with open(dest / TS_PRE_COMMIT_CONFIG_YAML, "w") as f:
        for line in lines:
            f.write(f"{line}\n")


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
    for hook_name in registry:
        if hook_name == "pre-commit-hooks":
            message += "check-yaml: true\n"
            message += "check-xml: true\n"
            continue
        hook = registry[hook_name]
        if hook.rule_type == RuleType.MANDATORY:
            message += f"{hook_name}: true\n"
        elif hook.rule_type == RuleType.OPT_OUT:
            arg = getattr(args, f"no_{hook_name.replace('-', '_')}", False)
            message += f"{hook_name}: {'false' if arg else 'true'}\n"
        elif hook.rule_type == RuleType.OPT_IN:
            arg = getattr(args, f"with_{hook_name.replace('-', '_')}", False)
            message += f"{hook_name}: {'true' if arg else 'false'}\n"
        else:
            raise RuntimeError(
                f"Unrecognized hook type: {hook.rule_type!r} for {hook_name}."
            )
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

    hook_names = []
    for hook_name in registry:
        if hook_name == "pre-commit-hooks":
            hook_names.append("check-yaml")
            hook_names.append("check-xml")
            continue
        hook_names.append(hook_name)

    # Check if all hooks are in the .ts_pre_commit_config.yaml config file,
    # except possibly for the optional ones.
    missing_hooks = _check_missing_hooks(config, hook_names)

    # Check if all mandatory hooks are in the .ts_pre_commit_config.yaml config
    # file.
    incorrect_config_options = _check_incorrect_config_options(config, hook_names)

    # Check that no superfluous hooks are in the .ts_pre_commit_config.yaml
    # config file.
    additional_hooks = _check_additional_hooks(config, hook_names)

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


def _check_missing_hooks(config: dict, hook_names: list[str]) -> list[str]:
    missing_hooks = []
    for hook_name in hook_names:
        missing = True
        for option in config:
            if option == hook_name:
                missing = False
                break

        # Make sure to skip check-yaml and check-xml.
        if hook_name not in registry:
            continue

        hook = registry[hook_name]
        if hook.rule_type != RuleType.MANDATORY:
            missing = False
        if missing:
            missing_hooks.append(hook_name)
    return missing_hooks


def _check_incorrect_config_options(config: dict, hook_names: list[str]) -> list[str]:
    incorrect_config_options = []
    for hook_name in hook_names:
        # Make sure to skip check-yaml and check-xml.
        if hook_name not in registry:
            continue

        # Skip optional hooks.
        hook = registry[hook_name]
        if hook.rule_type != RuleType.MANDATORY:
            continue

        incorrect_config_option = True
        for option in config:
            if option == hook_name and config[option] is True:
                incorrect_config_option = False
                break
        if incorrect_config_option:
            incorrect_config_options.append(hook_name)
    return incorrect_config_options


def _check_additional_hooks(config: dict, hook_names: list[str]) -> list[str]:
    additional_hooks = []
    for option in config:
        additional_hook = True
        for hook_name in hook_names:
            if option == hook_name:
                additional_hook = False
        if additional_hook:
            additional_hooks.append(option)
    return additional_hooks


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

    for hook_name in registry:
        hook = registry[hook_name]
        if hook.rule_type == RuleType.OPT_OUT:
            option = config.get(hook_name, True)
            setattr(args, f"no_{hook_name.replace('-', '_')}", not option)
        elif hook.rule_type == RuleType.OPT_IN:
            option = config.get(hook_name, False)
            setattr(args, f"with_{hook_name.replace('-', '_')}", option)


def generate_pre_commit_conf_file(args: types.SimpleNamespace) -> None:
    """Generate the '.pre-commit-config.yaml' file. Both the contents and the
    destination path are determined from the provided args.

    Parameters
    ----------
    args : `types.SimpleNamespace`
        The args that determine the contents and the destination path.
    """
    dest = _get_dest(args=args)
    overwrite = True if "overwrite" in vars(args) and args.overwrite else False
    pre_commit_config = "repos:"
    for hook_name in registry:
        hook = registry[hook_name]
        if hook.rule_type == RuleType.MANDATORY:
            pre_commit_config += hook.pre_commit_config
        elif hook.rule_type == RuleType.OPT_OUT:
            arg = getattr(args, f"no_{hook_name.replace('-', '_')}", False)
            pre_commit_config += hook.pre_commit_config if not arg else ""
        elif hook.rule_type == RuleType.OPT_IN:
            arg = getattr(args, f"with_{hook_name.replace('-', '_')}", False)
            pre_commit_config += hook.pre_commit_config if arg else ""
    pre_commit_config_filename = pathlib.Path(dest) / PRE_COMMIT_CONFIG_FILE_NAME
    _write_pre_commit_config_file(
        overwrite, pre_commit_config, pre_commit_config_filename
    )


def _write_pre_commit_config_file(
    overwrite: bool, pre_commit_config: str, pre_commit_config_filename: pathlib.Path
) -> None:
    if pre_commit_config_filename.exists() and not overwrite:
        print(f"Not overwriting existing {pre_commit_config_filename}")
    else:
        create_overwrite = "Creating"
        if pre_commit_config_filename.exists():
            create_overwrite = "Overwriting existing"
        print(f"{create_overwrite} {pre_commit_config_filename}.")
        with open(pre_commit_config_filename, "w") as f:
            f.write(pre_commit_config)


def create_config_files(args: types.SimpleNamespace) -> None:
    """Create the pre-hook config files. The provided args are used to
    determine which files to create and which destination path to create them
    in.

    Parameters
    ----------
    args : `types.SimpleNamespace`
        The args that determine which files get created and which destination
        path to create them in.
    """
    dest = _get_dest(args=args)
    overwrite = True if "overwrite" in vars(args) and args.overwrite else False
    for hook_name in registry:
        hook = registry[hook_name]
        if hook.config_file_name:
            hook_config_file_name = dest / hook.config_file_name
            if hook_config_file_name.exists() and not overwrite:
                print(f"Not overwriting existing {hook_config_file_name}")
                continue
            create_overwrite = "Creating"
            if hook_config_file_name.exists():
                create_overwrite = "Overwriting existing"

            match hook.rule_type:
                case RuleType.MANDATORY:
                    _write_mandatory(hook, hook_config_file_name, create_overwrite)
                case RuleType.OPT_OUT:
                    _write_opt_in(
                        args, hook_name, hook, hook_config_file_name, create_overwrite
                    )
                case RuleType.OPT_IN:
                    _write_opt_out(
                        args, hook_name, hook, hook_config_file_name, create_overwrite
                    )


def _write_mandatory(
    hook: PreCommitHookMetadata,
    hook_config_file_name: pathlib.Path,
    create_overwrite: str,
) -> None:
    assert hook.config is not None
    print(f"{create_overwrite} {hook_config_file_name}.")
    with open(hook_config_file_name, "w") as f:
        f.write(hook.config)


def _write_opt_in(
    args: types.SimpleNamespace,
    hook_name: str,
    hook: PreCommitHookMetadata,
    hook_config_file_name: pathlib.Path,
    create_overwrite: str,
) -> None:
    arg = getattr(args, f"no_{hook_name.replace('-', '_')}", False)
    if not arg:
        assert hook.config is not None
        print(f"{create_overwrite} {hook_config_file_name}.")
        with open(hook_config_file_name, "w") as f:
            f.write(hook.config)


def _write_opt_out(
    args: types.SimpleNamespace,
    hook_name: str,
    hook: PreCommitHookMetadata,
    hook_config_file_name: pathlib.Path,
    create_overwrite: str,
) -> None:
    arg = getattr(args, f"with_{hook_name.replace('-', '_')}", False)
    if arg:
        assert hook.config is not None
        print(f"{create_overwrite} {hook_config_file_name}.")
        with open(hook_config_file_name, "w") as f:
            f.write(hook.config)


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
        if len(dot_gitignore_contents) > 0 and dot_gitignore_contents[-1] != "\n":
            f.write("\n")
        if PRE_COMMIT_CONFIG_FILE_NAME not in dot_gitignore_contents:
            f.write(f"{PRE_COMMIT_CONFIG_FILE_NAME}\n")
        for hook_name in registry:
            hook = registry[hook_name]
            if (
                hook.config_file_name
                and hook.config_file_name not in dot_gitignore_contents
            ):
                f.write(f"{hook.config_file_name}\n")


async def run_pre_commit_install(args: types.SimpleNamespace) -> None:
    """Run the ``pre-commit install`` command.

    Parameters
    ----------
    args : `types.SimpleNamespace`
        The args that determine which destination path pre-commit is to be
        executed in.

    Raises
    ------
    `RuntimeError`
        In case the execution of pre-commit terminated unsuccessfully.
    """
    if "skip_pre_commit_install" in vars(args) and args.skip_pre_commit_install:
        print("Not running 'pre-commit install'.")
        return

    exe_path = shutil.which("pre-commit")
    if exe_path is None:
        raise AssertionError("Could not find pre-commit executable.")
    dest = _get_dest(args=args)

    # Get the current working directory for later reference.
    cwd = os.getcwd()

    # Change to the destination directory.
    os.chdir(dest)

    # Execute ``pre-commit install``
    process_args = ["pre-commit", "install"]
    process = await asyncio.create_subprocess_exec(
        *process_args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await process.communicate()
    message = stdout.decode().strip()

    # Return to the original working directory.
    os.chdir(cwd)

    # Handle the return code of the process.
    if process.returncode == 0:
        # Execution terminated successfully.
        print(message)
    else:
        # Execution terminated unsuccessfully.
        raise RuntimeError(message)


def generate_pre_commit_conf() -> None:
    """Main function that generates the .prec-ommit-config.yaml file. It also
    copies the required pre-commit hook config files and updates/creates the
    .gitignore file.
    """
    command_line_args = sys.argv[1:]
    try:
        args = parse_args(command_line_args=command_line_args)
        create_or_report_missing_config_file(args=args)
        validate_config_file_contents(args=args)
    except (ValueError, FileNotFoundError) as e:
        sys.exit(str(e))
    update_args_from_config_file(args=args)
    generate_pre_commit_conf_file(args=args)
    create_config_files(args=args)
    update_dot_gitignore(args=args)
    asyncio.run(run_pre_commit_install(args=args))
