#!/bin/bash
# This script stubs a typical file structure found in invenio repositories 
#  on travis CI to help testing the migration helper script

mkdir testrepo
cd testrepo

# Step 2
touch .travis.yml

# Step 3
echo "# Matches the exact files either package.json or .travis.yml" > .editorconfig
echo "[{package.json,.travis.yml}]" >> .editorconfig

# Step 4.1
echo ".. image:: https://img.shields.io/travis/inveniosoftware/invenio-oauthclient.svg" > README.rst
echo "        :target: https://travis-ci.org/inveniosoftware/invenio-oauthclient" >> README.rst

# Step 4.2
echo "https://travis-ci.com/inveniosoftware/invenio-oauthclient/pull_requests" > CONTRIBUTING.rst

# Step 5
echo "python -m check_manifest --ignore \".travis-*\" && \
python -m sphinx.cmd.build -qnNW docs docs/_build/html && \
docker-services-cli up ${DB}
python -m pytest
tests_exit_code=\$?
docker-services-cli down
exit \"\$tests_exit_code\"" > run-tests.sh

echo "[pytest]
addopts = --pep8 --ignore=docs --cov=invenio_formatter --cov-report=term-missing
filterwarnings = ignore::pytest.PytestDeprecationWarning" > pytest.ini
echo "include .tx/config
include *.txt
recursive-include docs *.bat
recursive-include docs Makefile" > MANIFEST.in

echo "tests_require = [
    \"check-manifest>=0.25\",
    \"coverage>=4.0\",
    \"isort>=4.2.2\",
    \"mock>=1.3.0\",
    \"pydocstyle>=1.0.0\",
    \"pytest-cov>=1.8.0\",
    \"pytest-pep8>=1.0.6\",
    \"pytest>=4.0.0,<5.0.0\",
]" > setup.py

echo "Created stub structure"