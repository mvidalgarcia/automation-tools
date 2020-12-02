# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import os
import shutil
import subprocess
from os import path

from automation_tools import config
from automation_tools.repositories import GithubUtils
from automation_tools.scripts.pip2020 import config as script_config
from automation_tools.utils import execute


def error_detector(repositories):
    """Detect the invenio modules that require fixing."""
    clean = []
    need_fix = []
    command_fails = []

    if path.exists(script_config.local_virtualenvs_path):
        shutil.rmtree(script_config.local_virtualenvs_path)
    else:
        os.mkdir(script_config.local_virtualenvs_path)

    for repository in repositories:
        print(f'------- WORKING ON {repository} -------')
        folder_repository = f'{script_config.local_virtualenvs_path}/{repository}'
        os.mkdir(folder_repository)

        subprocess.check_output(['virtualenv', '-p',
                                 script_config.python_version, folder_repository])
        try:
            outputs = []
            if script_config.flag_2020:
                command = [f'{folder_repository}/bin/pip',
                           'install', f'Invenio clones/{repository}',
                           '--use-feature=2020-resolver']

            else:
                command = [f'{folder_repository}/bin/pip',
                           'install', f'Invenio clones/{repository}']

            for out in execute(command):
                outputs.append(out.strip())

            if 'ERROR' in outputs:
                need_fix.append(repository)

            else:
                clean.append(repository)

        except:
            command_fails.append(repository)

        shutil.rmtree(folder_repository)

    return need_fix, clean, command_fails


def main():
    """."""
    invenio_repositories = GithubUtils.list_invenio_modules()
    if script_config.download_locally:
        GithubUtils.download_invenio_modules(invenio_repositories,
                                             config.local_repositories_path)

    need_fix, clean, command_fails = error_detector(invenio_repositories)

    print("Following repositories have to be fixed")
    for repositories in need_fix:
        print(repositories)

    print("Following repositories have failed")
    for repositories in command_fails:
        print(repositories)

    print("Following repositories are clean")
    for repositories in clean:
        print(repositories)


if __name__ == "__main__":
    main()
