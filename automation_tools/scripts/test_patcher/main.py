# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
import os

from automation_tools.repositories import LocalRepository
from automation_tools.scripts.test_patcher import config as script_config
from automation_tools.utils import (file_path, index_of,
                                    list_local_repository_names, read_content,
                                    split_lines)


def apply_changes(repository):
    """Performs the changes on a repository."""
    filepath = file_path(repository, script_config.run_tests_sh)
    content = read_content(filepath)
    file = open(filepath, 'w')
    content_lines = split_lines(content)
    content_lines = list(map(lambda l: script_config.replacements[l] if l in script_config.replacements else l, content_lines))
    file.write(os.linesep.join(content_lines))
    file.close()

    filepath = file_path(repository, script_config.setup_cfg)
    content = read_content(filepath)
    file = open(filepath, 'w')
    content_lines = split_lines(content)

    i = 0
    while i < len(content_lines):
        if content_lines[i] == '[aliases]':
            assert (content_lines[i + 1] == 'test = pytest' or content_lines[i + 1] == 'test=pytest') \
                   and content_lines[i + 2] == ''
            del content_lines[i]
            del content_lines[i]
            del content_lines[i]
            break
        i += 1
    file.write(os.linesep.join(content_lines))
    file.close()

    with LocalRepository(repository) as repo:
        repo.github_process(
            script_config.open_pr,
            script_config.expected,
            repository,
            'master',  # Always work on local master
            script_config.remote_branch,
            script_config.message,
            script_config.title,
            script_config.body,
            script_config.base,
            script_config.commit_extra_before,
            script_config.commit_extra_after
        )


def main():
    count_total = 0
    count_with_runtests = 0
    count_with_test_command = 0
    count_test_substitutable = 0
    count_with_single_test_alias = 0

    to_patch = []

    for repository in list_local_repository_names():  # List all cloned repositories
        # Analyze `run-tests.sh`
        content = read_content(file_path(repository, script_config.run_tests_sh))
        if content:
            split = split_lines(content)

            test_substitutable = any(line in script_config.replacements for line in split)

            if test_substitutable:
                count_test_substitutable += 1

            has_pytest = any(s == 'pytest' or s.startswith('pytest ') or s.startswith('py.test ') for s in split)

            if test_substitutable or not has_pytest:
                count_with_test_command += 1

            count_with_runtests += 1

            # Analyze `setup.cfg`

            content = read_content(file_path(repository, script_config.setup_cfg))
            if test_substitutable and content:
                split = split_lines(content)
                cmdidx = index_of('test = pytest', split)
                if not cmdidx:
                    cmdidx = index_of('test=pytest', split)
                if cmdidx:
                    if split[cmdidx - 1] == '[aliases]':
                        if split[cmdidx + 1] == '':
                            # See https://github.com/inveniosoftware/flask-menu/blob/master/setup.py#L128
                            assert 'cmdclass' not in read_content(file_path(repository, script_config.setup_py))
                            if script_config.should_apply_changes(repository):
                                to_patch.append(repository)
                            count_with_single_test_alias += 1

        count_total += 1

    print('Total repositories:\t\t\t\t%s' % count_total)
    print('With file `run-tests.sh`:\t\t\t%s' % count_with_runtests)
    print('Uses a `test` command or related:\t\t%s' % count_with_test_command)
    print('Uses a command with a known substitution:\t%s' % count_test_substitutable)
    print('Defines one alias `test`:\t\t\t%s' % count_with_single_test_alias)
    print('Will be patched:\t\t\t\t%s out of %s patchable' % (len(to_patch), count_with_single_test_alias))

    print('')

    if len(to_patch) > 0:
        passcode = 'Yes'
        print('%s repositories will be patched. Type "%s" to confirm.' % (len(to_patch), passcode))
        if input() == passcode:
            for repository in to_patch:
                print('Patching %s...' % repository)
                apply_changes(repository)
            print('Done.')
        else:
            print('Aborting.')
    else:
        print('No modification was made.')


if __name__ == "__main__":
    main()
