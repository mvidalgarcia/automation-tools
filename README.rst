Automation tools
----------------

Management tools to perform modifications accross Invenio repositories.

Structure
~~~~~~~~~

The following Python scripts are fairly simple in terms of code. Some of
the functions are one-shot, which means they were quickly designed for a
task that had to be performed once. Nevertheless the code was written in
such a way that it should easily be modified to fit for a different
need. To do this you have to different options: - if your need is close
to one already implemented, you can adjust the related configuration of
the script - if your need is too different, you can create a new folder
including a new script with its related configuration

::

    .
    └── automation_tools
        ├── __init__.py
        ├── config.py
        ├── github_utils.py
        ├── scripts
        │   ├── pip2020
        │   │   ├── config.py
        │   │   └── main.py
        │   └── test_patcher
        │       ├── config.py
        │       └── main.py
        └── utils.py

Global configuration
~~~~~~~~~~~~~~~~~~~~

Below you can find an example of a working ``config.py``. You have to
modify any of the parameters to fit your current settings

.. code:: python

    # The organization name
    organization = "inveniosoftware"

    # Remote name
    destination = "origin"

    # Directory path to hold a copy of the repositories
    local_repositories_path = '/path/to/inveniosoftware_cache'

    # Github credentials / token
    github = Github('YOUR_GITHUB_TOKEN')

Test patcher
~~~~~~~~~~~~

The goal of this script is to update python setup.py test calls to
python -m pytest.

How it works
^^^^^^^^^^^^

For the vast majority of repositories, there are two modifications to
make:

1. Remove alias from setup.cfg (remove the [aliases] declaration aswell
   if there are no other aliases)
2. Update run-tests.sh to perform python -m pytest

How to configure it
^^^^^^^^^^^^^^^^^^^

Below you can find an example of a working ``config.py``. Some
parameters should not be modified if you want to keep the current
behavior of the script: - run\_tests\_sh - setup\_cfg - setup\_py -
expected

| However, you have to fill the Github settings in order to match your
configuration.
| As well, you can modify the ``replacements`` parameters to perform
other modifications.

.. code:: python

    def should_apply_changes(repository):
        """Configure what repository should take the changes."""
        return True

    # Substitutions to be made in `run-tests.sh`
    replacements = {
        'python setup.py test': 'python -m pytest',
        'python setup.py test && \\': 'python -m pytest && \\',
        'python setup.py test # && \\': 'python -m pytest # && \\',
    }

    # File names
    run_tests_sh = 'run-tests.sh'
    setup_cfg = 'setup.cfg'
    setup_py = 'setup.py'


    # Github config

    # Mode:
    # - False: push to repository
    # - True: push to repository + open PR
    open_pr = True

    # Remote branch to push to
    remote_branch = "test-command"

    base = "master"

    # Message of the commit / Title of the PR (if applicable) / Body of the PR (if applicable)
    message = "tests: bypass setuptools and use pytest"
    title = message
    body = "Modification of the repository to use pytest instead of setuptools"

    # `git [extra_before] commit ...`
    commit_extra_before = []  # eg. ['-c', 'user.name=invenio-toaster-bot', '-c', 'user.email=hseif@foryourrecords.com']
    # `git ... commit ... [extra_after]`
    commit_extra_after = []  # eg. ['--no-gpg-sign']

    # Expected file modifications (safety check)
    expected = [
            'M run-tests.sh',
            'M setup.cfg'
            ]

PIP2020
~~~~~~~

The goal of this script is to try out the new flag for PIP2020 ``'--use-feature=2020-resolver``
and identify the packages that will fail once it is released. This is configurable to use it as
well with the current installer if needed.

How it works
^^^^^^^^^^^^

It is performing the following actions:

1. Listing the invenio repositories
2. Downloarding them if required
3. Installing them and sorting them according to their status

How to configure it
^^^^^^^^^^^^^^^^^^^

Below you can find an example of a working ``config.py``. You have to
modify any of the parameters to fit your current settings

.. code:: python

    # Set the local path to install virtual environments
    local_virtualenvs_path = 'Virtualenvs'

    # Set python version to create virtualenv
    python_version = 'python3.6'

    # Download locally the packages you want to test
    download_locally = False

    # Use the new pip2020 resolver
    flag_2020 = True