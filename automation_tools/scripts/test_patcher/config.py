# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Script configuration."""

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
