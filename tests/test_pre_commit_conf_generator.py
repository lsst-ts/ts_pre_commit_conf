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
import tempfile
import types
import unittest

from lsst.ts.pre_commit_conf.pre_commit_conf_generator import (
    FLAKE8_CONFIG_FILE,
    ISORT_CONFIG_FILE,
    MYPY_CONFIG_FILE,
    PRE_COMMIT_CONFIG_FILE_NAME,
    copy_config_files,
    generate_pre_commit_conf_file,
    parse_args,
    update_dot_gitignore,
)

ROOT = pathlib.Path(__file__)

# Directories with data used by this script.
TEMPLATES_DIR = ROOT.resolve().parents[0] / "templates"

# Data dir.
DATA_DIR = ROOT.resolve().parents[0] / "data"

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
        assert args.dest == "."

        args = parse_args(command_line_args=["--no-mypy"])
        assert args.no_mypy is True
        assert args.dest == "."

        args = parse_args(command_line_args=["--dest", "/tmp"])
        assert args.no_mypy is False
        assert args.dest == "/tmp"

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
        args = types.SimpleNamespace()
        for key, value in kwargs.items():
            setattr(args, key, value)
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
        # Nominal cases where all pre-commit hooks are included.
        for kwargs in (dict(), dict(no_mypy=False)):
            self.validate_pre_commit_conf(
                expected_conf_file=PRE_COMMIT_CONF_COMPLETE, **kwargs  # type: ignore
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
        args = types.SimpleNamespace()
        for key, value in kwargs.items():
            setattr(args, key, value)
        with tempfile.TemporaryDirectory() as tmpdirname:
            # Set destination path to avoid left over files from running the
            # unit tests.
            args.dest = tmpdirname

            copy_config_files(args=args)

            # Assert that the number of files in the destination directory
            # equals the number of expected files.
            dest_glob = pathlib.Path(tmpdirname).glob("**/*")
            dest_files = [f for f in dest_glob]
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
                FLAKE8_CONFIG_FILE,
                ISORT_CONFIG_FILE,
                MYPY_CONFIG_FILE,
            ]
            self.validate_config_files(
                expected_conf_files=expected_conf_files, **kwargs  # type: ignore
            )

        # Exclude mypy.
        expected_conf_files = [FLAKE8_CONFIG_FILE, ISORT_CONFIG_FILE]
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
        args = types.SimpleNamespace()
        for key, value in kwargs.items():
            setattr(args, key, value)
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
