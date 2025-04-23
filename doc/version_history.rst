.. py:currentmodule:: lsst.ts.pre_commit_conf

.. _lsst.ts.pre_commit_conf.version_history:

###############
Version History
###############

v0.9.14 (2025-04-22)
====================

New Features
------------

- Switched to towncrier. (`DM-48659 <https://rubinobs.atlassian.net//browse/DM-48659>`_)


Bug Fixes
---------

- Fixed package version module generation. (`DM-48659 <https://rubinobs.atlassian.net//browse/DM-48659>`_)


Performance Enhancement
-----------------------

- Update the versions of the black, clang-format, flake8, isort, mypy, pre-commit-hooks, ruff and towncrier hooks. (`DM-48659 <https://rubinobs.atlassian.net//browse/DM-48659>`_)

.. towncrier release notes start

v0.9.14
=======

* Update the versions of the black, clang-format, flake8, isort, mypy, pre-commit-hooks, ruff and towncrier hooks.

v0.9.13
=======

* Update the versions of the black, clang-format, flake8, mypy and ruff hooks.

v0.9.12
=======

* Make sure that existing hook config file names are not added to .gitignore a second time.

v0.9.11
=======

* Make sure that unused hook config file names do not show up in .gitignore anymore.

v0.9.10
=======

* Remove reference to mamba from README.

v0.9.9
======

* Update the Jira URL in the towncrier configuration.
* Update the versions of the clang, pre-commit and ruff hooks.

v0.9.8
======

* Update the version of ts-conda-build to 0.4 in the conda recipe.

v0.9.7
======

* Update the versions of the following hooks:

  * black
  * clang-format
  * flake8
  * mypy
  * ruff

v0.9.6
======

* Code improvements following SonarLint.
* Make sure that not-included hooks do not get added to gitignore.

v0.9.5
======

* Update the versions of several hooks.

v0.9.4
======

* Add types-python-dateutils to mypy additional_dependencies.

v0.9.3
======

* Update the versions of several hooks.
* Make sure that hook config files get created/overwritten or skipped for hooks with "-" in the name.

v0.9.2
======

* Make sure that .pre-commit-config.yaml doesn't get overwritten unless --overwrite is specified.

v0.9.1
======

Update the versions of the following hooks:

  * black
  * clang-format
  * mypy
  * pre-commit-hooks
  * ruff
  * towncrier

v0.9.0
======

* Mark all mandatory hooks as such.
* Change default behavior to not overwrite existing hook config files.
  Also add a command line option to force overwriting existing hook config files.

v0.8.0
======

* Refactor how exclusion/inclusion of pre-commit hooks is managed.

  Instead of having 2 flags (optional and excludable) to control how a rule is managed, use an enumeration.
  For now, the enumeration specifies 3 types of rules; mandatory, opt-out, opt-in.

  Mandatory rules, as the name say, cannot be excluded.
  opt-out rules are included by default but can be excluded.
  opt-in rules as excluded by default and can be included.

* Add new pre-commit hook for towncrier.

v0.7.4
======

* Make the clang format pre-commit hook excludable.

v0.7.3
======

* Disabling running "pre-commit install" no longer requires an explicit "true".

v0.7.2
======

* Update ruff configuration and the black and ruff pre-commit hook versions.
* Allow for disabling running "pre-commit install".
  This is necessary for the CI jobs in Jenkins.
  Developers should not use this option, which is why the option has a long name.

v0.7.1
======

* Add ``pre-commit`` as test and runtime dependency.

v0.7.0
======

* Make sure that ``pre-commit install`` is executed when ``generate_pre_commit_conf`` is.

v0.6.1
======

* Make sure that optional hooks really are optional.

v0.6.0
======

* Update versions of pre-commit hooks.
* Simplify adding new hooks.
* Add new hooks:

  * format-xmllint
  * ruff

v0.5.1
======

* Ignore missing clang-format line in config file.

v0.5.0
======

* clang-format pre-commit check.

v0.4.4
======

* Fix the conda build.


v0.4.3
======

* Update the version of mypy.


v0.4.2
======

* Add Jenkinsfile for CI builds.
* Add Jenkinsfile.conda for Conda builds.


v0.4.1
======

* Refer to the TSSW Developer Guide for usage instructions.


v0.4.0
======

* Update versions of pre-commit hooks.
* Rely on .ts_pre_commit_config.yaml for configuring the pre-commit hooks.


v0.3.0
======

* Add the ``check-xml`` hook.


v0.2.0
======

* Remove the ``--no-isort`` command line option.
* Make sure that the MyPy config file name always gets added .gitignore.


v0.1.0
======

First release of the project

This version includes:

* Configuration files for flake8, isort and mypy.
* Templates for generating a .pre-commit-config.yaml file.
* A script that generates the .pre-commit-config.yaml file and copies the configuration files for flake8, isort and mypy to ther specified destination.
