##################
ts_pre_commit_conf
##################

``ts_pre_commit_conf`` is a tool to generate configuration files for the ``pre-commit`` hooks for the Telescope and Site SoftWare (TSSW) team at the Vera C. Rubin Observatory.

These configuration files facilitate ``pre-commit`` to maintain ``black`` formatting, ``flake8`` compliance and ``isort`` imports sorting.
If ``mypy`` is used, a configuration file can be generated for that as well.
The configuration files are generated by using the ``generate_pre_commit_conf`` command.
Since TSSW uses ``conda`` for their software installations, a conda recipe was created for this project and the conda package was made available in the ``lsstts`` conda channel.

For usage information, see the `TSSW Developer Guide`_.

.. _TSSW Developer Guide: https://tssw-developer.lsst.io/procedures/pre_commit.html
