#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2020, f100024.

import json
import os
import re

# Ansible imports
from ansible.module_utils.basic import AnsibleModule
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen


DOCUMENTATION = '''
---
module: check_python_package_version
version_added: "not added"
short_description: Check python requirements for lastest version vi PyPi API
extends_documentation_fragment: files
description:
    - Check python requirements for newer versions using PyPi API
options:
  dependencies:
      description:
          - Set path to files with requirements list
      required: true
      type: list
'''

EXAMPLES = '''
- hosts: localhost
  connection: local
  tasks:
  - name: Check python deps
    check_python_package_version:
      dependencies:
        - "{{ playbook_dir }}/test_requirements.txt"
'''


def get_latest_version(package_name):
    """
    Using PyPI API to obtain package information
    URI: https://pypi.org/pypi/[package_name]/json
    info.version
    :return: version from PyPi API for package_name
    """

    result = 'git:// in package_name'
    if 'git://' not in package_name:
        uri = 'https://pypi.org/pypi/{}/json'.format(package_name)
        response = urlopen(uri)
        result = '{uri} - {response_code}'.format(uri=uri,
                                                  response_code=response.code)
        if response.code == 200:
            response_json = json.loads(response.read())
            result = response_json['info']['version']
        response.close()
    return result


def parse_string(package_requirement):
    """
    Parse string with requirements
    :return: [Package name], [Comparing sign], [Package version]
    """

    m = re.match('(.*)(==)(.*)', package_requirement)
    if m:
        return m.groups()[0], m.groups()[1], m.groups()[2]
    if 'git://' not in package_requirement:
        return package_requirement, '', ''
    return '', '', ''


def compare(local_version, latest_version, comparing_sign):
    """
    Compare package version from PyPi API and value parsed
    from file with requirements.
    :local_version: current package version
    :latest_version: real package version
    :comparing_sign: comparing sign parsed from file with requirements
    :return: boolean value
    """
    dictionary_comparing = {
       '==': local_version == latest_version,
    }
    return dictionary_comparing[comparing_sign]


def get_results(dependency_list):
    """
    :dependecy_list: list with packages from requirements files
    :return: sorted and compared packages list with state of condition
    """
    formatted_result_list = []
    for dependency in dependency_list:
        package_name, comparing_sign, local_version = parse_string(dependency)
        if not package_name or not local_version:
            continue
        latest_version = get_latest_version(package_name)
        if compare(local_version, latest_version, comparing_sign):
            formatted_result_list.append(
                '[+] {package_name}: local: {local} pypi latest version: {latest}'
                .format(package_name=package_name, local=local_version,
                        latest=latest_version))
        else:
            formatted_result_list.append(
                '[-] {package_name}: local: {local} pypi latest version: {latest}'
                .format(package_name=package_name, local=local_version,
                        latest=latest_version))
    return sorted(formatted_result_list)


def parse_dependency(file_path):
    """
    :file_path: path to file with requirements
    :return: `dependencies_list` from `file_path` and nested files
    """

    dependencies_list = []
    dirname_file_path = os.path.dirname(file_path)
    with open(file_path, 'r') as temp_file:
        opened_dependency_file = temp_file.readlines()

    for dependency in opened_dependency_file:
        if dependency.startswith('-r'):
            dependency_path = \
                os.path.join(dirname_file_path, dependency.replace('-r', '').strip())

            if not os.path.isfile(dependency_path):
                print('File {} does not exist'.format(dependency_path))
                continue

            # Try get dependencies from nested dependency file
            dependencies_list.extend(parse_dependency(dependency_path))
        else:
            dependencies_list.append(dependency.strip())
    return dependencies_list


def get_consolidated_dependencies_list(dependencies_path_list):
    """
    :list_file_path: path to file with requirements
    :return: all parsed files
    """

    full_dependencies_list = []
    for dependency_file in dependencies_path_list:
        if not os.path.isfile(dependency_file):
            print('File {} does not exist'.format(dependency_file))
            continue
        # Open files and create list of deps
        full_dependencies_list.extend(
            parse_dependency(dependency_file)
        )
    return list(set(full_dependencies_list))


def main():
    """
    Main section
    """

    module = AnsibleModule(
        argument_spec=dict(
            dependencies=dict(required=True, type=list)),
        supports_check_mode=True)
    dependencies = get_consolidated_dependencies_list(module.params['dependencies'])
    result_list = get_results(dependencies)
    module.exit_json(msg='Finished', text='\n' + '\n'.join(result_list))


if __name__ == '__main__':
    main()
