# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import os
import subprocess
from os import path

from automation_tools import config


def file_path(repository, filename):
    """Absolute file path inside a repository."""
    return path.join(config.local_repositories_path, repository, filename)


def read_content(filepath):
    """Returns the content of a file as a string if it exists or None."""
    if path.exists(filepath):
        return open(filepath, 'r').read()
    else:
        return None


def split_lines(content):
    """Returns a list of strings corresponding to the lines of this string."""
    return content.split(os.linesep)


def index_of(string, values):
    """Returns the array index of a given value if it exists or None."""
    try:
        return values.index(string)
    except ValueError:
        return None

def execute(cmd):
    """Snippet from https://stackoverflow.com/questions/4417546/constantly-print-subprocess-output-while-process-is-running."""
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line 
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def list_directory_names(parent_directory):
    """List directory names inside the parent directory."""
    if path.exists(parent_directory) and os.path.isdir(parent_directory):
        return next(os.walk(parent_directory))[1]
    else:
        raise Exception()


def list_local_repository_names():
    """List locally cloned repositories."""
    return list_directory_names(config.local_repositories_path)
