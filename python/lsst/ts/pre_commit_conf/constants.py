import pathlib

# The root of the current file to be used by the Path definitions below.
ROOT = pathlib.Path(__file__)

# Directories with data used by this script.
CONFIG_FILES_DIR = ROOT.resolve().parents[0] / "config_files"
TEMPLATES_DIR = ROOT.resolve().parents[0] / "templates"

# Config files for the pre-commit hooks.
FLAKE8_CONFIG_FILE_NAME = ".flake8"
ISORT_CONFIG_FILE_NAME = ".isort.cfg"
MYPY_CONFIG_FILE_NAME = ".mypy.ini"
PRE_COMMIT_CONFIG_FILE_NAME = ".pre-commit-config.yaml"

# Config file paths for the pre-commit hooks.
FLAKE8_CONFIG_FILE = CONFIG_FILES_DIR / FLAKE8_CONFIG_FILE_NAME
ISORT_CONFIG_FILE = CONFIG_FILES_DIR / ISORT_CONFIG_FILE_NAME
MYPY_CONFIG_FILE = CONFIG_FILES_DIR / MYPY_CONFIG_FILE_NAME

# Template files.
ISORT_PRE_COMMIT_HOOK_TEMPLATE = TEMPLATES_DIR / "isort-pre-commit-hook-template.yaml"
MYPY_PRE_COMMIT_HOOK_TEMPLATE = TEMPLATES_DIR / "mypy-pre-commit-hook-template.yaml"
PFLAKE8_PRE_COMMIT_HOOK_TEMPLATE = (
    TEMPLATES_DIR / "pflake8-pre-commit-hook-template.yaml"
)
PRE_COMMIT_CONFIG_TEMPLATE = TEMPLATES_DIR / "pre-commit-config-template.yaml"
ISORT_PYPROJECT_TEMPLATE = TEMPLATES_DIR / "isort-pyproject.toml"
MYPY_PYPROJECT_TEMPLATE = TEMPLATES_DIR / "mypy-pyproject.toml"
PFLAKE8_PYPROJECT_TEMPLATE = TEMPLATES_DIR / "pflake8-pyproject.toml"

DOT_GITIGNORE = ".gitignore"
