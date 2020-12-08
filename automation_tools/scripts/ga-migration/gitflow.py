import logging, pygit2
import os
import main
from github import Github
from pygit2 import GIT_SORT_TOPOLOGICAL, GIT_SORT_REVERSE, Signature
import subprocess

logging.basicConfig(level=logging.INFO)
local_repositories_path = "./localrepos"
GA_BRANCH_NAME = "ga-migration"

# List of repositories
repositories = ["jsonresolver"]

# Clone

url_github = "https://github.com/"
org_name = "inveniosoftware"
repository_name = repositories[0]

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
main.pipeline(f"{local_repositories_path}/{repository_name}")

# git add .
subprocess.run(
    f"git add .",
    shell=True,
    check=True,
    cwd=f"{local_repositories_path}/{repository_name}",
)

# git commit
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
subprocess.run(
    f"git push --set-upstream origin ga-migration",
    shell=True,
    check=True,
    cwd=f"{local_repositories_path}/{repository_name}",
)


# Create the Pull Request on GitHub
pr = gh_repo.create_pull(
    title="Migrate to GH Actions",
    body="This PR was produced by an automated action.",
    head=GA_BRANCH_NAME,
    base="master",
)
