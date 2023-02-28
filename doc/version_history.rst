.. py:currentmodule:: lsst.ts.pre_commit_conf

.. _lsst.ts.pre_commit_conf.version_history:

###############
Version History
###############

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
