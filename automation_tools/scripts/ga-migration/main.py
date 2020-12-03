import os
import logging
import fileinput
import re
import click

logging.basicConfig(level=logging.DEBUG)


def deleteFile(filepath):
    """
    If a file exists, delete it
    """
    logging.info("TASK: Deleting %s" % filepath)
    if os.path.isfile(filepath):
        logging.info("Found %s" % filepath)
        os.remove(filepath)
        logging.info("Deleted %s" % filepath)
    else:
        logging.info("No %s found" % filepath)


def replaceSimple(text, replacing, filepath):
    """
    Replaces every match of a string with another in the specified file
    """
    logging.info("TASK: Simple replacing %s with %s in %s" % (text, replacing, filepath))
    if os.path.isfile(filepath):
        logging.info("Found %s" % filepath)
        # TODO: expose number of matches
        with fileinput.FileInput(filepath, inplace=True, backup=".bak") as file:
            for line in file:
                print(line.replace(text, replacing), end="")
    else:
        logging.info("No %s found" % filepath)


def replaceRE(regex, output, filepath):
    """
    Replaces every match of a string with another in the specified file
    """
    logging.info("TASK: RegEx replacing %s with %s in %s" % (regex, output, filepath))
    if os.path.isfile(filepath):
        logging.info("Found %s" % filepath)
        # TODO: expose number of matches
        with fileinput.FileInput(filepath, inplace=True, backup=".bak") as file:
            for line in file:
                print(re.sub(regex, output, line), end="")
    else:
        logging.info("SKIPPED TASK. No %s found" % filepath)


@click.command()
@click.option("--targetpath", default=".", help="Target repo directory path")
def pipeline(targetpath):
    """Helps the migration from Travis CI pipelines
    to GitHub Actions running some common tasks"""

    # TODO: add the trailing slash only if needed
    targetpath = targetpath + "/"
    # Reference: https://codimd.web.cern.ch/TOOkF5yhSAKJq3TiY0L42A?view
    # Step 2
    deleteFile(targetpath + ".travis.yml")
    # Step 3
    replaceSimple(targetpath + ".travis.yml", ".github/workflows/*.yml", ".editorconfig")
    # Step 4.1
    replaceRE(
        r"https:\/\/img\.shields\.io\/travis\/([a-z]*\/[a-z-]*)\.svg",
        "https://github.com/\\1/workflows/CI/badge.svg",
        targetpath + "README.rst",
    )
    replaceRE(
        r"https:\/\/travis-ci\.org\/([a-z]*\/[a-z-]*)",
        "https://github.com/\\1/actions?query=workflow%3ACI",
        targetpath + "README.rst",
    )
    # Step 4.2
    replaceRE(
        r"https:\/\/travis-ci\.com\/([a-z]*\/[a-z-]*)\/pull_requests",
        "https://github.com/\\1/actions?query=event%3Apull_request",
        targetpath + "CONTRIBUTING.rst",
    )
    # Step 5
    replaceSimple(
        'check_manifest --ignore ".travis-*"',
        'check_manifest --ignore ".*-requirements.txt"',
        targetpath + "run-tests.sh",
    )


if __name__ == "__main__":
    pipeline()
