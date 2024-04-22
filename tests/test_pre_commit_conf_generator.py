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

import asyncio
import logging
import pathlib
import tempfile
import types
import unittest
from copy import copy

import pytest
import yaml
from lsst.ts import pre_commit_conf

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class PrecommitConfGeneratorTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_parse_args_no_command_line_args(self) -> None:
        args = pre_commit_conf.parse_args(command_line_args=[])
        assert args.no_mypy is False
        assert args.create is False
        assert args.dest == "."

        # Specifying --no-mypy without --create results in a ValueError.
        with pytest.raises(ValueError):
            pre_commit_conf.parse_args(command_line_args=["--no-mypy"])

        args = pre_commit_conf.parse_args(command_line_args=["--no-mypy", "--create"])
        assert args.no_mypy is True
        assert args.create is True
        assert args.dest == "."

        args = pre_commit_conf.parse_args(command_line_args=["--create"])
        assert args.no_mypy is False
        assert args.create is True
        assert args.dest == "."

        args = pre_commit_conf.parse_args(command_line_args=["--dest", "/tmp"])
        assert args.no_mypy is False
        assert args.create is False
        assert args.dest == "/tmp"

    def create_args(self, **kwargs: bool | str) -> types.SimpleNamespace:
        args = types.SimpleNamespace()
        for key, value in kwargs.items():
            setattr(args, key, value)
        return args

    async def test_create_or_report_missing_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdirname:
            args = self.create_args(dest=tmpdirname, create=False, no_mypy=False)
            with pytest.raises(FileNotFoundError):
                pre_commit_conf.create_or_report_missing_config_file(args=args)
            config_path = (
                pathlib.Path(tmpdirname) / pre_commit_conf.TS_PRE_COMMIT_CONFIG_YAML
            )
            assert not config_path.exists()

            args = self.create_args(dest=tmpdirname, create=True, no_mypy=False)
            pre_commit_conf.create_or_report_missing_config_file(args=args)
            config_path = (
                pathlib.Path(tmpdirname) / pre_commit_conf.TS_PRE_COMMIT_CONFIG_YAML
            )
            assert config_path.exists()
            with open(config_path, "r") as f:
                config = f.read()
            for hook_name in pre_commit_conf.registry:
                if hook_name == "pre-commit-hooks":
                    # This hook is not part of TS_PRE_COMMIT_CONFIG_YAML.
                    continue
                assert hook_name in config
                assert f"{hook_name}: true" in config

    async def test_validate_config_file_contents(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdirname:
            args = self.create_args(dest=tmpdirname, create=True, no_mypy=False)
            config_path = (
                pathlib.Path(tmpdirname) / pre_commit_conf.TS_PRE_COMMIT_CONFIG_YAML
            )
            pre_commit_conf.create_or_report_missing_config_file(args=args)

            # No error should be raised.
            pre_commit_conf.validate_config_file_contents(args=args)

            # Now changes/additions are made to the config file which should
            # result in errors.
            modifications = [
                {"test": True},
                {"isort": False},
                {"isort": False, "test": True},
            ]
            for mods in modifications:
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f)
                for key in mods:
                    config[key] = mods[key]
                with open(config_path, "w") as f:
                    f.write(yaml.safe_dump(config))
                with pytest.raises(ValueError):
                    pre_commit_conf.validate_config_file_contents(args=args)

        with tempfile.TemporaryDirectory() as tmpdirname:
            args = self.create_args(dest=tmpdirname, create=True, no_mypy=False)
            config_path = (
                pathlib.Path(tmpdirname) / pre_commit_conf.TS_PRE_COMMIT_CONFIG_YAML
            )
            pre_commit_conf.create_or_report_missing_config_file(args=args)
            # Removing a key should result in an error too.
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            config.pop("isort")
            with open(config_path, "w") as f:
                f.write(yaml.safe_dump(config))
            with pytest.raises(ValueError):
                pre_commit_conf.validate_config_file_contents(args=args)

    async def test_update_args_from_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdirname:
            args = self.create_args(
                dest=tmpdirname,
                create=True,
                no_mypy=False,
                with_clang_format=True,
                with_format_xmlint=True,
                with_ruff=True,
                with_towncrier=True,
                with_format_xmllint=True,
            )
            orig_args = copy(args)
            config_path = (
                pathlib.Path(tmpdirname) / pre_commit_conf.TS_PRE_COMMIT_CONFIG_YAML
            )
            pre_commit_conf.create_or_report_missing_config_file(args=args)

            pre_commit_conf.update_args_from_config_file(args)
            assert args == orig_args

            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            config["mypy"] = False
            with open(config_path, "w") as f:
                f.write(yaml.safe_dump(config))

            pre_commit_conf.update_args_from_config_file(args)
            assert args != orig_args

    def validate_pre_commit_conf(
        self, expected_hook_names: list[str], **kwargs: bool
    ) -> None:
        """Validate the generated .pre-commit-config.yaml file.

        Parameters
        ----------
        expected_hook_names : `list` of `str`
            The names of the PreCommitHookMetadata instances that contain the
            .pre-commit-config.yaml file contents.
        kwargs : `bool`
            Boolean values that indicate whether certain options should be
            included in the .pre-commit-config.yaml file. Currently supported
            are

                * no_mypy
        """
        print(kwargs)
        args = self.create_args(**kwargs)
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Set destination path to avoid left over files from running the
            # unit tests.
            args.dest = tmpdirname

            pre_commit_conf.generate_pre_commit_conf_file(args=args)
            pre_commit_conf_yaml_file = (
                pathlib.Path(tmpdirname) / pre_commit_conf.PRE_COMMIT_CONFIG_FILE_NAME
            )
            with open(pre_commit_conf_yaml_file) as f:
                generated_conf = f.read()
            for expected_hook_name in expected_hook_names:
                expected_hook = pre_commit_conf.registry[expected_hook_name]
                expected_pre_commit_config = expected_hook.pre_commit_config
                assert (
                    expected_pre_commit_config in generated_conf
                ), f"Expected: {expected_pre_commit_config}\n Got: {generated_conf}"
            for expected_hook_name in pre_commit_conf.registry:
                if expected_hook_name not in expected_hook_names:
                    expected_hook = pre_commit_conf.registry[expected_hook_name]
                    expected_pre_commit_config = expected_hook.pre_commit_config
                    arg_prefix = (
                        "no"
                        if expected_hook.rule_type
                        == pre_commit_conf.pre_commit_hooks.RuleType.OPT_OUT
                        else "with"
                    )
                    modifier_flag = kwargs.get(
                        f"{arg_prefix}_{expected_hook_name}",
                        expected_hook.rule_type
                        == pre_commit_conf.pre_commit_hooks.RuleType.OPT_OUT,
                    )
                    if (
                        expected_hook.rule_type
                        == pre_commit_conf.pre_commit_hooks.RuleType.OPT_OUT
                    ):
                        modifier_flag = not modifier_flag
                    if (
                        expected_hook.rule_type
                        != pre_commit_conf.pre_commit_hooks.RuleType.MANDATORY
                        and not modifier_flag
                    ):
                        assert expected_pre_commit_config not in generated_conf
                    else:
                        assert (
                            expected_pre_commit_config in generated_conf
                        ), f"Expected: {expected_pre_commit_config}\n to be in \n {generated_conf}."

    async def test_generate_pre_commit_conf(self) -> None:
        # Nominal case where all pre-commit hooks are included.
        self.validate_pre_commit_conf(
            expected_hook_names=["flake8", "isort", "mypy"],
            no_mypy=False,
        )

        # Exclude mypy.
        self.validate_pre_commit_conf(
            expected_hook_names=["flake8", "isort"],
            no_mypy=True,
        )

    def validate_config_files(
        self, expected_hook_names: list[str], **kwargs: bool
    ) -> None:
        """Validate that the copied configuration files for the pre-commit
        hooks are the expected ones both by name and number as well as by
        content.

        Parameters
        ----------
        expected_hook_names : `list` of `str`
            The names of the PreCommitHookMetadata instances that contain the
            pre-commit hook config file contents.
        kwargs : `bool`
            Boolean values that indicate whether certain config file should be
            copied or not. Currently supported are

                * no_mypy
        """
        args = self.create_args(**kwargs)
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Set destination path to avoid left over files from running the
            # unit tests.
            args.dest = tmpdirname

            pre_commit_conf.create_config_files(args=args)

            # Assert that the number of files in the destination directory
            # equals the number of expected files.
            dest_glob = pathlib.Path(tmpdirname).glob("**/*")
            dest_files = list(dest_glob)
            assert len(dest_files) == len(expected_hook_names)

            # Assert that the names and contents of the files in the
            # destination folder match those of the expected files.
            for expected_hook_name in expected_hook_names:
                expected_hook = pre_commit_conf.registry[expected_hook_name]
                filename = expected_hook.config_file_name
                expected_path = pathlib.Path(tmpdirname) / filename
                assert expected_path.exists()
                with open(expected_path) as dest:
                    dest_contents = dest.read()
                    assert expected_hook.config == dest_contents

    async def test_create_config_files(self) -> None:
        # Nominal cases where all pre-commit hooks are included.
        for kwargs in (dict(), dict(no_mypy=False)):
            print(kwargs)
            expected_hook_names = ["flake8", "isort", "mypy"]
            self.validate_config_files(
                expected_hook_names=expected_hook_names, **kwargs  # type: ignore
            )

        # Exclude mypy.
        expected_hook_names = ["flake8", "isort"]
        self.validate_config_files(
            expected_hook_names=expected_hook_names, no_mypy=True
        )

    def validate_overwrite(self, **kwargs: bool) -> None:
        """Validate that the existing hook config files are overwritten on not
        depending on the presence of the 'overwrite' argument.

        Parameters
        ----------
        kwargs : `bool`
            Boolean values that indicate whether hook config files should be
            overwritten or not.
        """
        args = self.create_args(**kwargs)
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Set destination path to avoid left over files from running the
            # unit tests.
            args.dest = tmpdirname

            flake8_hook = pre_commit_conf.registry["flake8"]
            flake8_hook_config_file_name = (
                pathlib.Path(tmpdirname) / flake8_hook.config_file_name
            )
            with open(flake8_hook_config_file_name, "w") as f:
                f.write(flake8_hook.config)
                # Add an extra line so we can verify whether the file was
                # overwritten or not.
                f.write("test = true")

            pre_commit_conf.create_config_files(args=args)

            with open(flake8_hook_config_file_name, "r") as f:
                flake8_lines = f.read()
                if "overwrite" in kwargs:
                    assert flake8_lines == flake8_hook.config
                else:
                    assert flake8_lines != flake8_hook.config

    async def test_overwrite(self) -> None:
        self.validate_overwrite()
        self.validate_overwrite(overwrite=True)

    def validate_dot_gitignore(self, **kwargs: bool) -> None:
        """Validate the generated .gitignore file.

        Parameters
        ----------
        kwargs : `bool`
            Boolean values that indicate whether certain options should be
            included in the .gitignore file. Currently supported are

                * no_mypy
        """
        args = self.create_args(**kwargs)
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Set destination path to avoid left over files from running the
            # unit tests.
            args.dest = tmpdirname

            pre_commit_conf.update_dot_gitignore(args=args)
            dot_gitignore_file = (
                pathlib.Path(tmpdirname) / pre_commit_conf.DOT_GITIGNORE
            )
            with open(dot_gitignore_file) as f:
                generated_dot_gitignore = f.read()
            for hook_name in pre_commit_conf.registry:
                if pre_commit_conf.registry[hook_name].config_file_name:
                    include = True
                    hook = pre_commit_conf.registry[hook_name]
                    if (
                        hook.rule_type == pre_commit_conf.RuleType.OPT_OUT
                        and hook.config_file_name
                    ):
                        include = not getattr(
                            args, f"no_{hook_name.replace('-', '_')}", False
                        )
                    elif (
                        hook.rule_type == pre_commit_conf.RuleType.OPT_IN
                        and hook.config_file_name
                    ):
                        include = getattr(
                            args, f"no_{hook_name.replace('-', '_')}", False
                        )
                    if include:
                        assert (
                            pre_commit_conf.registry[hook_name].config_file_name
                            in generated_dot_gitignore
                        )
                    else:
                        assert (
                            pre_commit_conf.registry[hook_name].config_file_name
                            not in generated_dot_gitignore
                        )
            # Make sure that no entries were added for hooks without a config
            # file.
            assert "None" not in generated_dot_gitignore

    async def test_update_dot_gitignore(self) -> None:
        # Nominal cases where all pre-commit hooks are included. Note that the
        # MyPy config file name always gets added.
        for kwargs in (dict(), dict(no_mypy=False), dict(no_mypy=True)):
            self.validate_dot_gitignore(**kwargs)  # type: ignore

    async def test_run_pre_commit_install(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdirname:
            args = self.create_args(dest=tmpdirname)

            # First try in an empty directory. This should fail.
            with pytest.raises(RuntimeError):
                await pre_commit_conf.run_pre_commit_install(args=args)

            # Initialize a git repo and try again. Now it should work.
            git_args = ["git", "init", tmpdirname]
            process = await asyncio.create_subprocess_exec(*git_args)
            await process.wait()
            await pre_commit_conf.run_pre_commit_install(args=args)
