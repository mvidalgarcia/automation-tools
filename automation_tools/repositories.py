# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""GitHub utilities."""

import os
import shutil
import subprocess
import sys
from os import path

import pygit2

from automation_tools import config
from automation_tools.config import github
from automation_tools.utils import execute


class GithubUtils(object):
    @staticmethod
    def list_invenio_modules():
        """List invenio modules by parsing inveniosoftware organization."""
        organization = 'inveniosoftware'
        try:
            user = github.get_organization(organization)
            invenio_repositories = [repository.name for repository in user.get_repos() \
                                    if repository.name.startswith('invenio-')]
            return invenio_repositories

        except:
            print('Failed to process the request')

    @staticmethod
    def list_organization_repositories(organization):
        """List repositories by parsing configured organization."""
        try:
            user = github.get_organization(organization)
            invenio_repositories = [repository.name for repository in user.get_repos()]
            return invenio_repositories

        except:
            print('Failed to process the request')

    @staticmethod
    def download_invenio_modules(repositories, local_repositories_path):
        """Download all the invenio modules in a newly created subfolder."""
        if path.exists(local_repositories_path):
            raise Exception("Folder already exists")

        os.mkdir(local_repositories_path)
        url_github = "https://github.com/inveniosoftware"
        for repository_name in repositories:
            pygit2.clone_repository(f"{url_github}/{repository_name}", f"{local_repositories_path}/{repository_name}")

    @staticmethod
    def open_pr(gh_repository, title, body, branch, base):
        """Open PR with previous changes"""
        try:
            gh_repository.create_pull(
                title=title,
                body=body,
                head=branch,
                base=base
            )
            pr_opened = True
        except:
            pr_opened = False

        return pr_opened

    @staticmethod
    def create_organization_repository(repository):
        """Creates a repository under the organization name."""
        org = config.github.get_organization(config.organization)
        org.create_repo(repository)


class LocalRepository(object):
    """Context for a local copy of a repository."""
    def __init__(self, repository):
        self.repository = repository

    def __enter__(self):
        self.previous_directory = os.getcwd()
        os.chdir(path.join(config.local_repositories_path, self.repository))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.previous_directory)

    def check_status(self, expected):
        """Check if modifications are the ones expected."""
        outputs = []
        for out in execute(["git", "status", "-s"]):
            outputs.append(out.strip())

        if outputs == expected:
            modifs_ok = True

        else:
            modifs_ok = False

        return modifs_ok

    def commit(self, message, extra_before=None, extra_after=None):
        """Commit if changes."""
        try:
            subprocess.check_output(["git", "add", "."])
            commit = ["git"]
            if extra_before:
                commit.extend(extra_before)
            commit.extend(["commit", "-m", message])
            if extra_after:
                commit.extend(extra_after)
            subprocess.check_output(commit)
            commited = True
        except:
            commited = False

        return commited

    def push(self, destination, local_branch, remote_branch, force=False):
        """Push commited changes."""
        try:
            push = ["git", "push", destination, local_branch + ':' + remote_branch]
            if force:
                push.extend(['--force'])
            subprocess.check_output(push)
            pushed = True
        except:
            pushed = False

        return pushed

    def github_process(self, is_mode_pr, expected, repository, local_branch, remote_branch, message, title, body, base,
                       commit_extra_before, commit_extra_after):
        """."""
        modifs_ok = self.check_status(expected)
        if modifs_ok:
            print("Has to be committed")
            committed = self.commit(message, commit_extra_before, commit_extra_after)
            if committed:
                print("Has been committed")
                pushed = self.push(config.destination, local_branch, remote_branch)
                if not pushed:
                    raise Exception("Failed to push")

                if pushed and is_mode_pr:
                    print("Has been pushed")
                    gh_repository = github.get_repo(f"{config.organization}/{repository}")
                    pr_opened = GithubUtils.open_pr(gh_repository, title, body, remote_branch, base)
                    if pr_opened:
                        print("PR has been opened")
                    else:
                        raise Exception("PR has not been opened")
            else:
                raise Exception("Failed to commit")

        else:
            raise Exception("Please review modifications")

    def set_origin(self, new_origin_url):
        """Set a repository's origin."""
        execute(["git", "remote", "set-url", config.destination, new_origin_url])
