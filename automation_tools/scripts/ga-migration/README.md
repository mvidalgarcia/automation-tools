# ga-migration

## Install

```console
$ virtualenv ~/.virtualenvs/ga-migration
$ source ~/.virtualenvs/ga-migration/bin/activate
$ pip install -r requirements.txt
```

## Migration

Apply migration patches on a cloned repository:

```bash
# e.g.
# git clone https://github.com/inveniosoftware/invenio-charts-js
python main.py --targetpath=invenio-charts-js
```

To apply migration on a list of cloned repositories, specified as `REPO_PATHS_TO_MIGRATE` in `config.py`:

```bash
python main.py
```

## Full pipeline

Run the whole pipeline given a repository name inside the `inveniosoftware` github org:

```bash
GH_ACCESS_TOKEN=$TOKEN python gitflow.py --reponame=invenio-charts-js
```

Get a GitHub access token at https://github.com/settings/tokens/new

This will:

- Clone the repository
- Look for the most recent commit where `.travis.yml` was still present
- Checkout a new branch from that commit
- Apply the [migration](#migration) patches
- Add the modifications and commit them
- Push the new `ga-migrate` branch to the github origin
- Look for a migration Issue
	- If it's not there, it will open a new one
- Open a PR to merge `ga-migrate` to `master`, linking the migration Issue