import logging, pygit2
import os
import main
from github import Github
from pygit2 import GIT_SORT_TOPOLOGICAL, GIT_SORT_REVERSE, Signature
import subprocess
import click

logging.basicConfig(level=logging.INFO)
local_repositories_path = "./localrepos"
GA_BRANCH_NAME = "ga-migration"


def fullgit(repository_name):
    # Clone
    url_github = "https://github.com/"
    org_name = "inveniosoftware"

    # Setup GitHub
    #  Get an access token at https://github.com/settings/tokens/new
    #  and set it as env variable
    #  e.g. start the script as `GH_ACCESS_TOKEN=$TOKEN python gitflow.py`
    g = Github(os.environ["GH_ACCESS_TOKEN"])

    # TODO: Check if folder already exists
    logging.info(f"Cloning {url_github}{org_name}/{repository_name}..")

    repo = pygit2.clone_repository(
        f"{url_github}{org_name}/{repository_name}",
        f"{local_repositories_path}/{repository_name}",
    )

    gh_repo = g.get_repo(f"{org_name}/{repository_name}")

    # Walk commits
    for commit in repo.walk(repo.head.target, GIT_SORT_TOPOLOGICAL):
        repo.checkout_tree(commit)
        logging.info(f"Checking out {commit.tree_id}")
        if os.path.isfile(
            f"{local_repositories_path}/{repository_name}/.travis.yml"
        ):
            print("found .travis.yml")
            break

    logging.info(f"Branching to {GA_BRANCH_NAME}..")

    # TODO: If the branch already exists, append a number
    #  and update GA_BRANCH_NAME
    repo.branches.local.create(GA_BRANCH_NAME, commit)

    subprocess.run(
        f"git checkout {GA_BRANCH_NAME}",
        shell=True,
        check=True,
        cwd=f"{local_repositories_path}/{repository_name}",
    )

    # Apply the patches
    main.migrate_repo(f"{local_repositories_path}/{repository_name}")

    # git add .
    subprocess.run(
        f"git add .",
        shell=True,
        check=True,
        cwd=f"{local_repositories_path}/{repository_name}",
    )

    # git commit
    logging.info(f"Committing the changes..")
    subprocess.run(
        f"git commit -m 'Migrate from Travis CI to GitHub Actions'",
        shell=True,
        check=True,
        cwd=f"{local_repositories_path}/{repository_name}",
    )

    # Switch from the HTTPS remote to the SSH one,
    #  to allow non-interactive passwordless push if a key is available
    #  TODO: just clone from the SSH origin from the beginning
    subprocess.run(
        f"git remote set-url origin git@github.com:{org_name}/{repository_name}.git",
        shell=True,
        check=True,
        cwd=f"{local_repositories_path}/{repository_name}",
    )

    # Push the new ga-migration branch
    logging.info(f"Pushing branch '{GA_BRANCH_NAME}'")
    subprocess.run(
        f"git push --set-upstream origin ga-migration",
        shell=True,
        check=True,
        cwd=f"{local_repositories_path}/{repository_name}",
    )

    # Look for the GA-migration issue
    open_issues = gh_repo.get_issues(state="open")
    number = 0
    for issue in open_issues:
        if (
            "migration to ga" in issue.title.lower()
            or "migration to github" in issue.title.lower()
        ):
            number = issue.number
            logging.info(
                f"Found the issue tracking the migration.. (#{number})"
            )

    if number == 0:
        issue = gh_repo.create_issue(
            title="global: migration to github-actions from travis"
        )
        number = issue.number
        logging.info(f"Created issue {issue}")

    # Create the Pull Request on GitHub
    pr = gh_repo.create_pull(
        title="Migrate to GH Actions",
        body=f"This PR was prepared by an [automated action](https://github.com/inveniosoftware/automation-tools/tree/master/automation_tools/scripts/ga-migration). Closes #{number}",
        head=GA_BRANCH_NAME,
        base="master",
    )
    logging.info(f"Created Pull Request on GitHub {pr}")


@click.command()
@click.option("--reponame", help="Repository name")
def pipeline(reponame):
    fullgit(reponame)


if __name__ == "__main__":
    pipeline()
