import click
import requests

from utils import (
    replace_regex,
    replace_simple,
    replace_list,
    read_yaml,
    download_file,
    delete_line,
    file_contains,
    append_to_file,
    add_line,
    delete_file,
    render_template,
    build_template,
)

from config import (
    GA_PYPI_PUBLISH_YAML_URL,
    GA_TESTS_YAML_URL,
    REPO_PATHS_TO_MIGRATE,
)


def migrate_repo(path):
    """Perform migration to repo on given path."""

    click.secho(f"\n>>> Migrating {path}...", fg="green")

    repo = path.split("/")[-1]
    repo_underscores = repo.replace("-", "_")

    # TODO: add the trailing slash only if needed
    path = path + "/"
    # Reference: https://codimd.web.cern.ch/TOOkF5yhSAKJq3TiY0L42A?view

    travis = read_yaml(path + ".travis.yml")
    if travis and travis["deploy"]["provider"] == "pypi":
        # Download pypi-publish.yml template
        download_file(
            GA_PYPI_PUBLISH_YAML_URL,
            path + ".github/workflows/pypi-publish.yml",
        )

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

    # tests.yaml
    build_template(repo, "tests.yml", path=f"{path}/.github/workflows")
    # run-tests.sh
    build_template(repo, "run-tests.sh", path=path)

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

    # Upgrade Sphinx 1 to 3 in setup.py
    replace_regex(
        r"Sphinx>=1.[0-9].[0-9]",
        "Sphinx>=3",
        path + "setup.py",
    )

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
            "pydocstyle",
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

    # Remove bak files
    delete_file(path + "*.bak")


# @click.command()
# @click.option("--targetpath", help="Target repo directory path")
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
