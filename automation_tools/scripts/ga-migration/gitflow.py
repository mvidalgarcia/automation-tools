import logging, pygit2
import os
import main
from github import Github

logging.basicConfig(level=logging.INFO)
local_repositories_path = "./localrepos"
GA_BRANCH_NAME = "ga-migration"

# List of repositories
repositories = ["invenio-formatter"]

# Clone

url_github = "https://github.com/inveniosoftware"

repository_name = repositories[0]

logging.info(f"Cloning {url_github}/{repository_name}..")
repo = pygit2.clone_repository(
    f"{url_github}/{repository_name}",
    f"{local_repositories_path}/{repository_name}",
)

gh_repo = g.get_repo(f"{url_github}/{repository_name}")

# Check if .travis.yml exists
if os.path.isfile(f"{local_repositories_path}/{repository_name}/.travis.yml"):
    logging.info(f".travis.yml found")
else:
    # Walk commits
    for commit in repo.walk(repo.head.target, GIT_SORT_TOPOLOGICAL):
        repo.checkout(commit)
        if os.path.isfile(
            f"{local_repositories_path}/{repository_name}/.travis.yml"
        ):
            pass

# Branch
new_branch = repo.branches.local.create(GA_BRANCH_NAME)

# Apply the patches
main.pipeline(f"{local_repositories_path}/{repository_name}")

# Git add
index = repo.index
index.add(".")
index.write()

# Git commit
author = Signature("Alice Author", "alice@authors.tld")
committer = Signature("Cecil Committer", "cecil@committers.tld")
tree = repo.TreeBuilder().write()
repo.create_commit(
    "refs/heads/master",  # the name of the reference to update
    author,
    committer,
    "one line commit message\n\ndetailed commit message",
    tree,  # binary string representing the tree object ID
    [],  # list of binary strings representing parents of the new commit
)

# Git push
# TODO

# Open PR
pr = repo.create_pull(
    title="Migrate to GH Actions",
    body="",
    head=GA_BRANCH_NAME,
    base="master",
)
