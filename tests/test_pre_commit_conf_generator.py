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

import logging
import pathlib
import shutil
import tempfile
import types
import unittest
from copy import copy

import pytest
import yaml
from lsst.ts.pre_commit_conf.pre_commit_conf_generator import (
    CLANG_FORMAT_CONFIG_FILE,
    FLAKE8_CONFIG_FILE,
    ISORT_CONFIG_FILE,
    MYPY_CONFIG_FILE,
    PRE_COMMIT_CONFIG_FILE_NAME,
    TS_PRE_COMMIT_CONFIG_YAML,
    copy_config_files,
    create_or_report_missing_config_file,
    generate_pre_commit_conf_file,
    parse_args,
    update_args_from_config_file,
    update_dot_gitignore,
    validate_config_file_contents,
)

ROOT = pathlib.Path(__file__)

# Directories with data used by this script.
TEMPLATES_DIR = ROOT.resolve().parents[0] / "templates"

# Data dir.
DATA_DIR = ROOT.resolve().parents[0] / "data"

# ts_pre_commit_config config files for validation.
TS_PRE_COMMIT_CONFIG_COMPLETE = DATA_DIR / "ts_pre_commit_config_complete.yaml"

# pre-commit config files for validation.
PRE_COMMIT_CONF_COMPLETE = DATA_DIR / "pre_commit_conf_complete.yaml"
PRE_COMMIT_CONF_WITHOUT_MYPY = DATA_DIR / "pre_commit_conf_without_mypy.yaml"

# .gitignore files for validation.
DOT_GITIGNORE_COMPLETE = DATA_DIR / "dot_gitignore_complete"
DOT_GITIGNORE_WITHOUT_MYPY = DATA_DIR / "dot_gitignore_without_mypy"

logging.basicConfig(
    format="%(asctime)s:%(levelname)s:%(name)s:%(message)s", level=logging.DEBUG
)


class PrecommitConfGeneratorTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_parse_args_no_command_line_args(self) -> None:
        args = parse_args(command_line_args=[])
        assert args.no_mypy is False
        assert args.create is False
        assert args.dest == "."

        # Specifying --no-mypy without --create results in a ValueError.
        with pytest.raises(ValueError):
            args = parse_args(command_line_args=["--no-mypy"])

        args = parse_args(command_line_args=["--no-mypy", "--create"])
        assert args.no_mypy is True
        assert args.create is True
        assert args.dest == "."

        args = parse_args(command_line_args=["--create"])
        assert args.no_mypy is False
        assert args.create is True
        assert args.dest == "."

        args = parse_args(command_line_args=["--dest", "/tmp"])
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
                create_or_report_missing_config_file(args=args)
            config_path = pathlib.Path(tmpdirname) / TS_PRE_COMMIT_CONFIG_YAML
            assert not config_path.exists()

            args = self.create_args(dest=tmpdirname, create=True, no_mypy=False)
            create_or_report_missing_config_file(args=args)
            config_path = pathlib.Path(tmpdirname) / TS_PRE_COMMIT_CONFIG_YAML
            assert config_path.exists()
            with open(config_path, "r") as f:
                config = f.read()
            with open(TS_PRE_COMMIT_CONFIG_COMPLETE, "r") as f:
                expected = f.read()
            assert config == expected

    async def test_validate_config_file_contents(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdirname:
            args = self.create_args(dest=tmpdirname, create=False, no_mypy=False)
            config_path = pathlib.Path(tmpdirname) / TS_PRE_COMMIT_CONFIG_YAML
            shutil.copy(TS_PRE_COMMIT_CONFIG_COMPLETE, config_path)

            # No error should be raised.
            validate_config_file_contents(args=args)

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
                    validate_config_file_contents(args=args)
                # Restore the config file so the modifications don't interfere
                # with the next checks.
                shutil.copy(TS_PRE_COMMIT_CONFIG_COMPLETE, config_path)

            # Removing a key should result in an error too.
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            config.pop("isort")
            with open(config_path, "w") as f:
                f.write(yaml.safe_dump(config))
            with pytest.raises(ValueError):
                validate_config_file_contents(args=args)

    async def test_update_args_from_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdirname:
            args = self.create_args(dest=tmpdirname, create=False, no_mypy=False)
            orig_args = copy(args)
            config_path = pathlib.Path(tmpdirname) / TS_PRE_COMMIT_CONFIG_YAML
            shutil.copy(TS_PRE_COMMIT_CONFIG_COMPLETE, config_path)

            update_args_from_config_file(args)
            assert args == orig_args

            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
            config["mypy"] = False
            with open(config_path, "w") as f:
                f.write(yaml.safe_dump(config))

            update_args_from_config_file(args)
            assert args != orig_args

    def validate_pre_commit_conf(
        self, expected_conf_file: pathlib.Path, **kwargs: bool
    ) -> None:
        """Validate the generated .pre-commit-config.yaml file.

        Parameters
        ----------
        expected_conf_file : `pathlib.Path`
            The Path where the .pre-commit-config.yaml file is written to.
        kwargs : `bool`
            Boolean values that indicate whether certain options should be
            included in the .pre-commit-config.yaml file. Currently supported
            are

                * no_mypy
        """
        args = self.create_args(**kwargs)
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Set destination path to avoid left over files from running the
            # unit tests.
            args.dest = tmpdirname

            generate_pre_commit_conf_file(args=args)
            pre_commit_conf_yaml_file = (
                pathlib.Path(tmpdirname) / PRE_COMMIT_CONFIG_FILE_NAME
            )
            with open(pre_commit_conf_yaml_file) as f:
                generated_conf = f.read()
            with open(expected_conf_file) as f:
                expected_conf = f.read()
            assert generated_conf == expected_conf

    async def test_generate_pre_commit_conf(self) -> None:
        # Nominal case where all pre-commit hooks are included.
        self.validate_pre_commit_conf(
            expected_conf_file=PRE_COMMIT_CONF_COMPLETE,
            no_mypy=False,
        )

        # Exclude mypy.
        self.validate_pre_commit_conf(
            expected_conf_file=PRE_COMMIT_CONF_WITHOUT_MYPY,
            no_mypy=True,
        )

    def validate_config_files(
        self, expected_conf_files: list[pathlib.Path], **kwargs: bool
    ) -> None:
        """Validate that the copied configuration files for the pre-commit
        hooks are the expected ones both by name and number as well as by
        content.

        Parameters
        ----------
        expected_conf_files : `list` of `pathlib.Path`
            The Paths where the pre-commit hook config files are written to.
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

            copy_config_files(args=args)

            # Assert that the number of files in the destination directory
            # equals the number of expected files.
            dest_glob = pathlib.Path(tmpdirname).glob("**/*")
            dest_files = list(dest_glob)
            assert len(dest_files) == len(expected_conf_files)

            # Assert that the names and contents of the files in the
            # destination folder match those of the expected files.
            for expected_conf_file in expected_conf_files:
                filename = expected_conf_file.name
                expected_path = pathlib.Path(tmpdirname) / filename
                assert expected_path.exists()
                with open(expected_conf_file) as orig, open(expected_path) as dest:
                    orig_contents = orig.read()
                    dest_contents = dest.read()
                    assert orig_contents == dest_contents

    async def test_copy_config_files(self) -> None:
        # Nominal cases where all pre-commit hooks are included.
        for kwargs in (dict(), dict(no_mypy=False)):
            expected_conf_files = [
                CLANG_FORMAT_CONFIG_FILE,
                FLAKE8_CONFIG_FILE,
                ISORT_CONFIG_FILE,
                MYPY_CONFIG_FILE,
            ]
            self.validate_config_files(
                expected_conf_files=expected_conf_files, **kwargs  # type: ignore
            )

        # Exclude mypy.
        expected_conf_files = [
            CLANG_FORMAT_CONFIG_FILE,
            FLAKE8_CONFIG_FILE,
            ISORT_CONFIG_FILE,
        ]
        self.validate_config_files(
            expected_conf_files=expected_conf_files,
            no_mypy=True,
        )

    def validate_dot_gitignore(
        self, expected_dot_gitignore_file: pathlib.Path, **kwargs: bool
    ) -> None:
        """Validate the generated .pre-commit-config.yaml file.

        Parameters
        ----------
        expected_dot_gitignore_file : `pathlib.Path`
            The Path where the .gitignore file is written to.
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

            update_dot_gitignore(args=args)
            dot_gitignore_file = pathlib.Path(tmpdirname) / ".gitignore"
            with open(dot_gitignore_file) as f:
                generated_dot_gitignore = f.read()
            with open(expected_dot_gitignore_file) as f:
                expected_dot_gitignore = f.read()
            assert generated_dot_gitignore == expected_dot_gitignore

    async def test_update_dot_gitignore(self) -> None:
        # Nominal cases where all pre-commit hooks are included. Note that the
        # MyPy config file name always gets added.
        for kwargs in (dict(), dict(no_mypy=False), dict(no_mypy=True)):
            self.validate_dot_gitignore(
                expected_dot_gitignore_file=DOT_GITIGNORE_COMPLETE, **kwargs  # type: ignore
            )
