import logging
import fileinput
import glob
import re
import os
import ast
import json
import subprocess

import requests
import yaml
from jinja2 import Environment, FileSystemLoader


logging.basicConfig(level=logging.INFO)

JinjaEnv = Environment(
    loader=FileSystemLoader(
        f"{os.path.join(os.path.dirname(__file__))}/templates"
    )
)


def get_repo_services(repo_name):
    """Get repository services."""

    def _grep_url(grep_options, term, url):
        """
        Perform grep operation against content hosted under URL.

        :return: Whether term matches.
        """
        return not bool(
            subprocess.call(
                f'grep {grep_options} -- "{term}" <(curl -s {url})',
                shell=True,
                executable="/bin/bash",
            )
        )

    repo_master_raw_url = (
        f"https://raw.githubusercontent.com/inveniosoftware/{repo_name}/master"
    )
    travis_raw_url = f"{repo_master_raw_url}/.travis.yml"
    is_migrated = not requests.get(travis_raw_url).ok

    if is_migrated:
        logging.info("TASK: Repo already migrated, rechecking services...")
        grep_options = "-qE"
        url = f"{repo_master_raw_url}/run-tests.sh"
        search_terms = {
            r"docker-services-cli up .*(DB|postgresql)": "db",
            r"docker-services-cli up .*(CACHE|redis)": "cache",
            r"docker-services-cli up .*(SEARCH|ES|\bes\b)": "search",
            r"docker-services-cli up .*(MQ|rabbitmq)": "mq",
        }
    else:
        logging.info("TASK: Repo not migrated, identifing services...")
        grep_options = "-q"
        url = travis_raw_url
        search_terms = {
            "postgres": "db",
            "- redis": "cache",
            "elasticsearch": "search",
            "rabbitmq-server": "mq",
        }

    services = dict()
    for term, service in search_terms.items():
        services[service] = _grep_url(grep_options, term, url)
    logging.info(f"TASK: Repo services identified: {services}")
    return services


def build_template(repo_name, template, path="."):
    """Build template based on repo services."""

    def create_file(content, destination):
        """Write content and create file in destination."""
        dirname = os.path.dirname(os.path.realpath(destination))
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        open(destination, "w").write(content)

    repo_services = get_repo_services(repo_name)
    has_services = any(repo_services.values())
    logging.info(f"TASK: Building and copying {template} template...")

    directory = "services" if has_services else "serviceless"

    content = render_template(f"{directory}/{template}", context=repo_services)
    destination = f"{path}/{template}"
    create_file(content, destination)


def render_template(template_file, context={}):
    """Return string content of specified template file."""
    template = JinjaEnv.get_template(template_file)
    output_from_parsed_template = template.render(**context)
    return output_from_parsed_template


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

    if os.path.isfile(filepath):
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
    else:
        logging.info("SKIPPED TASK. No %s found" % filepath)


def read_yaml(filepath):
    if os.path.isfile(filepath):
        logging.info("Found %s" % filepath)
        with open(filepath, "r") as stream:
            try:
                return yaml.safe_load(stream)

            except yaml.YAMLError as exc:
                print(exc)
    else:
        logging.info("SKIPPED TASK. No %s found" % filepath)
