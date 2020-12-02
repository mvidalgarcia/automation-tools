# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Contains the settings to repository modifications."""

from github import Github

# The organization name
organization = "inveniosoftware"

# Remote name
destination = "origin"

# Directory path to hold a copy of the repositories
local_repositories_path = '/path/to/inveniosoftware_cache'

# Github credentials / token
github = Github()
