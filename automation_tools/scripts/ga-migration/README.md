# ga-migration

## Install

```console
$ virtualenv ~/.virtualenvs/ga-migration
$ source ~/.virtualenvs/ga-migration/bin/activate
$ pip install -r requirements.txt
```

## Run

```console
# Migrate specific repo
$ python main.py --targetpath ../path/to/invenio/repo

# Migrate all repos on config.py
$ python main.py
```
