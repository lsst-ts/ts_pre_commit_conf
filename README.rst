##################
ts_pre_commit_conf
##################

``ts_pre_commit_conf`` contains configuration files for the tools used in the pre-commit hooks for the Telescope and Site SoftWare (TSSW) team at the Vera C. Rubin Observatory.


These configuration files facilitate ``pre-commit`` to maintain ``black`` formatting, ``flake8`` compliance and ``isort`` imports sorting.
The configuration files are downloaded by using the ``pre-commit-conf`` command from the ``centralized-pre-commit-conf`` project.
The maintainer of the ``centralized-pre-commit-conf`` project only makes available installation using ``pip``.
Since TSSW uses ``conda`` (or ``mamba``) for their software installations, a conda recipe was created for ``centralized-pre-commit-conf`` and the conda package was made available in the ``lsstts`` conda channel.
To enable this:

* Install pre-commit, for instance ``conda install -y pre-commit``.
* Install centralized-pre-commit-conf, for instance ``conda install -y -c lsstts centralized-pre-commit-conf``.
* Then either:

    * Download the ``config.yaml`` file from the ``develop`` directory in the ``develop`` branch on ``https://github.com/lsst-ts/ts_pre_commit_conf/`` and place it in ``~/.config/pre-commit-conf`` on UNIX systems (Linux and macOS).
    * Run ``pre-commit-conf -f`` once in every project to download the configuration files for pre-commit and add them to ``.gitignore``.

  OR

    * Download the configuration files using ``pre-commit-conf -f -r "https://raw.githubusercontent.com//lsst-ts/ts_pre_commit_conf/" -b "develop" -u -p "develop" -c .flake8 .isort.cfg .mypy.ini .pre-commit-config.yaml``

Note that the ``develop`` directory and the ``-p "develop"`` command line argument are referring to the same path in the ``ts_pre_commit_conf`` repo.
Other directories may be available as well.
The ``-b "develop"`` command line argument refers to the branch in the ``ts_pre_commit_conf`` repo.
For developers actively helping to maintain the configuration files, other branches can be used to pull the configuration files for testing purposes.
It is not recommended to use a different branch for other projects!

For more information about the use of the ``pre-commit-conf`` command, see the `centralized-pre-commit-conf <https://github.com/Pierre-Sassoulas/centralized-pre-commit-conf/>`_ homepage.
The ``appropriate search paths`` link on that page is wrong and should point `here <https://confuse.readthedocs.io/en/latest/usage.html#search-paths>`_.

The configuration files will be updated whenever the pre-commit hooks get updated.
The TSSW Jenkins CI jobs update these configuration files and execute pre-commit every time the jobs run, so you know that you need to update them locally and fix your code if a job fails.
