import fileinput
import glob
import logging
import re
import os
import ast
import json

import requests
import click

from config import (
    GA_PYPI_PUBLISH_YAML_URL,
    GA_TESTS_YAML_URL,
    REPO_PATHS_TO_MIGRATE,
)

logging.basicConfig(level=logging.INFO)


def delete_file(filepath):
    """
    If a file exists, delete it
    """
    logging.info("TASK: Deleting %s" % filepath)
    for file in glob.glob(filepath):
        if os.path.isfile(file):
            logging.info("Found %s" % file)
            os.remove(file)
            logging.info("Deleted %s" % file)
        else:
            logging.info("No %s found" % file)


def delete_line(term, filepath):
    """Delete file line contaning given term."""
    logging.info(f"TASK: Deleting line containing {term} in {filepath}")
    # import wdb; wdb.set_trace()
    if not os.path.isfile(filepath):
        logging.info("No %s found" % filepath)
    else:
        logging.info("Found %s" % filepath)
        with open(filepath, "r") as f:
            lines = f.readlines()
        with open(filepath, "w") as f:
            for line in lines:
                if term not in line:
                    f.write(line)
                else:
                    logging.info(f"TASK: Line deleted")


def file_contains(term, filepath):
    """Check whether file contains given term."""
    if not os.path.isfile(filepath):
        logging.info("No %s found" % filepath)
    else:
        with open(filepath) as f:
            return term in f.read()


def append_to_file(text, filepath):
    """Append text to file."""
    if not os.path.isfile(filepath):
        logging.info("No %s found" % filepath)
    else:
        with open(filepath, "a") as f:
            f.write(text)


def add_line(term, filepath):
    """ Add a line to a file """
    logging.info("TASK: Adding line '%s' to %s" % (term, filepath))
    # If the file exists
    if os.path.isfile(filepath):
        # And the line is not already there
        if not file_contains(term, filepath):
            append_to_file(term, filepath)
        else:
            logging.info("SKIPPED TASK. Line already there. ")
    else:
        logging.info("SKIPPED TASK. No %s found" % filepath)


def replace_simple(text, replacing, filepath):
    """
    Replaces every match of a string with another in the specified file
    """
    logging.info(
        "TASK: Simple replacing %s with %s in %s" % (text, replacing, filepath)
    )
    if os.path.isfile(filepath):
        logging.info("Found %s" % filepath)
        # TODO: expose number of matches
        with fileinput.FileInput(filepath, inplace=True, backup=".bak") as file:
            for line in file:
                print(line.replace(text, replacing), end="")
    else:
        logging.info("No %s found" % filepath)


def replace_regex(regex, output, filepath):
    """
    Replaces every match of a string with another in the specified file
    """
    logging.info(
        "TASK: RegEx replacing %s with %s in %s" % (regex, output, filepath)
    )
    if os.path.isfile(filepath):
        logging.info("Found %s" % filepath)
        # TODO: expose number of matches
        with fileinput.FileInput(filepath, inplace=True, backup=".bak") as file:
            for line in file:
                print(re.sub(regex, output, line), end="")
    else:
        logging.info("SKIPPED TASK. No %s found" % filepath)


def download_file(url, destination):
    # Get path
    dirname = os.path.dirname(os.path.realpath(destination))
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    print(dirname)
    r = requests.get(url, allow_redirects=True)
    open(destination, "wb").write(r.content)


def replace_list(filepath, regex, to_remove, to_add, var_name):
    """
    Given a python file, look for the "var_name" using "regex" and:
    - remove any occurence of the elements from the "to_remove" list
        partial matches allowed, e.g. pytest-cov will remove pytest-cov>=0.0.1
    - add the elements from the "to_add" list
    Write the changes to "var_name" variable in the original file
    """

    with open(filepath, "r") as f:
        contents = f.read()

    # Search the list in the file contents
    m = re.search(regex, contents)

    # Group 0 matches the whole assignment,
    # We need the right part of the assignment (Group 1)
    matched_list_str = m.group(1)

    # Deserialize it
    parsed_list = ast.literal_eval(matched_list_str)

    # Prepare the new list
    new_list = []

    for element in parsed_list:
        # Look for the package name
        pm = re.search(r"([0-9a-zA-Z-\[_\]]*)[><=]*", element)
        # If it doesn't match with any of the stuff we want to remove,
        #  add it to the new list
        if pm.group(1) not in to_remove:
            new_list.append(element)
        else:
            logging.info(f"Removed {element} from {var_name}")

    for el_to_add in to_add:
        if el_to_add not in parsed_list:
            new_list.append(el_to_add)
            logging.info(f"Added {el_to_add} in {var_name}")
        else:
            logging.info(f"{el_to_add} already in {var_name}")

    # Reconstruct the python assignment of the variable, with the list value
    #  Dump JSON with 4 spaces indent to keep setup.py formatted
    #  Must be kept in-sync with the indent_size value in
    #   .editorconfig / project setups
    py_new_string = f"{var_name} = {json.dumps(new_list, indent=4)}"

    # Replace the old (matched) list assignment with the one with the new contents
    content2 = contents.replace(m.group(0), py_new_string)

    # Overwrite the contents of the file
    with open(filepath, "w") as f:
        f.write(content2)


def migrate_repo(path):
    """Perform migration to repo on given path."""

    click.secho(f"\n>>> Migrating {path}...", fg="green")

    repo = path.split("/")[-1]
    repo_underscores = repo.replace("-", "_")

    # TODO: add the trailing slash only if needed
    path = path + "/"
    # Reference: https://codimd.web.cern.ch/TOOkF5yhSAKJq3TiY0L42A?view

    # .editorconfig
    replace_simple(
        path + ".travis.yml", ".github/workflows/*.yml", ".editorconfig"
    )

    # README.rst
    replace_regex(
        r"https:\/\/img\.shields\.io\/travis\/([a-z]*\/[a-z-]*)\.svg",
        "https://github.com/\\1/workflows/CI/badge.svg",
        path + "README.rst",
    )
    replace_regex(
        r"https:\/\/travis-ci\.org\/([a-z]*\/[a-z-]*)",
        "https://github.com/\\1/actions?query=workflow%3ACI",
        path + "README.rst",
    )

    # CONTRIBUTING.rst
    replace_regex(
        r"https:\/\/travis-ci\.(org|com)\/([a-z]*\/[a-z-]*)\/pull_requests",
        "https://github.com/\\2/actions?query=event%3Apull_request",
        path + "CONTRIBUTING.rst",
    )

    # run-tests.sh
    delete_line("isort", path + "run-tests.sh")
    replace_simple(
        'check-manifest --ignore ".travis-*"',
        'check-manifest --ignore ".*-requirements.txt"',
        path + "run-tests.sh",
    )

    # Download tests.yml template
    download_file(
        GA_TESTS_YAML_URL,
        path + ".github/workflows/tests.yml",
    )

    # Download pypi-publish.yml template
    download_file(
        GA_PYPI_PUBLISH_YAML_URL,
        path + ".github/workflows/pypi-publish.yml",
    )

    # pytest.ini
    delete_line("pep8ignore", path + "pytest.ini")
    replace_regex(
        "(addopts =).*",
        f'\\1 --isort --pydocstyle --pycodestyle --doctest-glob="*.rst" --doctest-modules --cov={repo_underscores} --cov-report=term-missing',
        path + "pytest.ini",
    )
    if not file_contains("testpaths", path + "pytest.ini"):
        append_to_file(
            f"testpaths = tests {repo_underscores}", path + "pytest.ini"
        )

    # Add .github/workflows *.yml to MANIFEST.in
    add_line("recursive-include .github/workflows *.yml", path + "MANIFEST.in")

    # Delete travis file
    delete_file(path + ".travis.yml")

    # Remove bak files
    delete_file(path + "*.bak")

    # Simplify setup.py test requirements replacing them with pytest-invenio
    replace_list(
        path + "setup.py",
        r"tests_require = (['\"\'[\s*\"(a-z-A-Z><=0-9.\[\]),]*])",
        [
            # Remove packages already installed by pytest-invenio
            "check-manifest",
            "coverage",
            "docker-services-cli",
            "pytest-celery",
            "pytest-cov",
            "pytest-flask",
            "pytest-isort",
            "pytest-pycodestyle",
            "pytest-pydocstyle",
            "pytest",
            "selenium",
            # pytest-pep8 is replaced by pytest-pycodestyle
            "pytest-pep8",
            # pytest-pep8 is replaced by pytest-isort
            "isort",
        ],
        ["pytest-invenio>=1.4.0"],
        "tests_require",
    )


@click.command()
@click.option("--targetpath", help="Target repo directory path")
def pipeline(targetpath):
    """Helps the migration from Travis CI pipelines
    to GitHub Actions running some common tasks"""

    if targetpath:
        migrate_repo(targetpath)
    else:
        for repo_path in REPO_PATHS_TO_MIGRATE:
            migrate_repo(repo_path)


if __name__ == "__main__":
    pipeline()
