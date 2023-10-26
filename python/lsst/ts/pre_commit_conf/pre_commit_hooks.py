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

__all__ = ["registry", "RuleType"]

import enum
from dataclasses import dataclass


class RuleType(enum.Enum):
    MANDATORY = enum.auto()
    OPT_IN = enum.auto()
    OPT_OUT = enum.auto()


@dataclass(eq=True, frozen=True)
class PreCommitHookMetadata:
    """Dataclass representing all metadata for a pre-commit hook.

    Attributes
    ----------
    pre_commit_config : `str`
        The YAML string to add to the pre-commit-config.yaml file.
    config_file_name : `str` | None
        The name of the configuration file. Set to None if no configuration
        file exists for this hook. The default is None.
    config : `str` | None
        The configuration of the pre-commit hook as contained by the
        configuration file. Set to None if no configuration file exists for
        this hook. The default is None.
    rule_type : `RuleType`
        Enumeration specifying what type of rule this is. This determines if
        a rule is mandatory, opt-in or opt-out.

    Notes
    -----
    Either both config_file_name and config need to be None or a string. This
    is checked.
    """

    pre_commit_config: str
    config_file_name: str | None = None
    config: str | None = None
    rule_type: RuleType = RuleType.MANDATORY

    def __post_init__(self) -> None:
        if (self.config_file_name is None and self.config is not None) or (
            self.config_file_name is not None and self.config is None
        ):
            raise RuntimeError(
                "Either both config_file_name and config need to be None or neither can be None."
            )


# Registry of pre-commit hooks alphabetically sorted by name.
registry = {
    "black": PreCommitHookMetadata(
        pre_commit_config="""
  - repo: https://github.com/psf/black
    rev: 23.10.1
    hooks:
      - id: black
""",
        rule_type=RuleType.MANDATORY,
    ),
    "clang-format": PreCommitHookMetadata(
        config_file_name=".clang-format",
        config="""Language: Cpp
BasedOnStyle: Google
ColumnLimit: 110
IndentWidth: 4
AccessModifierOffset: -4
SortIncludes: false
ConstructorInitializerIndentWidth: 8
ContinuationIndentWidth: 8
""",
        pre_commit_config="""
  - repo: https://github.com/pre-commit/mirrors-clang-format
    rev: v17.0.3
    hooks:
      - id: clang-format
""",
        rule_type=RuleType.OPT_IN,
    ),
    "flake8": PreCommitHookMetadata(
        config_file_name=".flake8",
        config="""[flake8]
extend-ignore = E133, E203, E226, E228, N802, N803, N806, N812, N813, N815, N816, W503
max-line-length = 110
max-doc-length = 79
exclude = __init__.py
""",
        pre_commit_config="""
  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
""",
        rule_type=RuleType.MANDATORY,
    ),
    "format-xmllint": PreCommitHookMetadata(
        pre_commit_config="""
  - repo: https://github.com/lsst-ts/pre-commit-xmllint
    rev: v1.0.0
    hooks:
      - id: format-xmllint
""",
        rule_type=RuleType.OPT_IN,
    ),
    "isort": PreCommitHookMetadata(
        config_file_name=".isort.cfg",
        config="""[settings]
profile=black
""",
        pre_commit_config="""
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        name: isort (python)
""",
        rule_type=RuleType.MANDATORY,
    ),
    "mypy": PreCommitHookMetadata(
        config_file_name=".mypy.ini",
        config="""[mypy]
disallow_untyped_defs = True
ignore_missing_imports = True
exclude = version.py
""",
        pre_commit_config="""
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.6.1
    hooks:
      - id: mypy
        additional_dependencies: [types-PyYAML==6]
""",
        rule_type=RuleType.OPT_OUT,
    ),
    "pre-commit-hooks": PreCommitHookMetadata(
        pre_commit_config="""
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: check-yaml
        exclude: conda/meta.yaml
      - id: check-xml
""",
        rule_type=RuleType.MANDATORY,
    ),
    "ruff": PreCommitHookMetadata(
        config_file_name=".ruff.toml",
        config="""ignore = [
  "E203", "E226", "E228", "E999", "N802", "N803", "N806", "N812", "N813", "N815", "N816"
]
line-length = 110
exclude = ["__init__.py"]
select = ["E", "F", "N", "W"]
[pycodestyle]
max-doc-length = 79
[pydocstyle]
convention = "numpy"
""",
        pre_commit_config="""
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.2
    hooks:
      - id: ruff
""",
        rule_type=RuleType.OPT_IN,
    ),
    "towncrier": PreCommitHookMetadata(
        pre_commit_config="""
  - repo: https://github.com/twisted/towncrier
    rev: 23.10.0
    hooks:
      - id: towncrier-check
      """,
        config_file_name="towncrier.toml",
        config="""[tool.towncrier]
package_dir = "python"
filename = "doc/version_history.rst"
directory = "doc/news"
filename_format = "{name}.{type}.rst|{name}.{type}.md"
title_format = "{version} ({project_date})"
issue_format = "`{issue} <https://jira.lsstcorp.org/browse/{issue}>`_"

[[tool.towncrier.type]]
    directory = "feature"
    name = "New Features"
    showcontent = true

[[tool.towncrier.type]]
    directory = "bugfix"
    name = "Bug Fixes"
    showcontent = true

[[tool.towncrier.type]]
    directory = "perf"
    name = "Performance Enhancement"
    showcontent = true

[[tool.towncrier.type]]
    directory = "doc"
    name = "Documentation"
    showcontent = true

[[tool.towncrier.type]]
    directory = "removal"
    name = "API Removal or Deprecation"
    showcontent = true

[[tool.towncrier.type]]
    directory = "misc"
    name = "Other Changes and Additions"
    showcontent = true
""",
        rule_type=RuleType.OPT_IN,
    ),
}
