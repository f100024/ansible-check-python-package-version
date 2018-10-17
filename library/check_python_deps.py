#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, f100024.

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
module: check_python_deps
version_added: "not added"
short_description: Check python requirements for newer versions
extends_documentation_fragment: files
description:
    - Check python requirements for newer versions using PyPi API
notes:
    - For executing requests using http://python-requests.org but
    should be updated soon
options:
  dependencies:
      description:
          - Set path to files with requirements list
      required: true
      type: list
  log:
      description:
          - Set path to module output with checked dependencies
      required: false
      type: str
'''

EXAMPLES = '''
- hosts: localhost
  connection: local
  tasks:
  - name: Check python deps
    check_python_deps:
      dependencies:
        - /test_requirements.txt
      log: "{{ playbook_dir }}/log.txt"
'''


def get_real_version(package_name):

    """
    Using PyPI API to obtain  package information
    URI: https://pypi.org/pypi/[package_name]/json
    info.version
    :return: version from PyPi API for package_name
    """

    result = 'git:// in package_name'
    if 'git://' not in package_name:
        request_str = 'https://pypi.org/pypi/{}/json'.format(package_name)
        r = urlopen(request_str)
        result = '{request_str} - {status_code}'.format(request_str=request_str, status_code=r.code)
        if r.code == 200:
            rjson = json.loads(r.read())
            result = rjson['info']['version']
        r.close()
    return result


def parse_req_string(tstring):

    """
    Parse string with requirements
    :return: [Package name], [Comparing sign], [Package version]
    """

    m = re.match('(.*)(>=|<=|==|>|<)(.*)', tstring)
    if m:
        return m.groups()[0], m.groups()[1], m.groups()[2]
    if 'git://' not in tstring:
        return tstring, '', ''
    return '', '', ''


def compare(cversion, rversion, s):

    """
    Compare package version from PyPi API and value parsed
    from file with requirements.

    :cversion: current package version
    :rversion: real package version
    :s: comparing sign parsed from file with requirements
    :return: boolean value
    """

    if cversion == 'latest':
        return True
    res = {
        '>=': cversion >= rversion,
        '<=': cversion <= rversion,
        '==': cversion == rversion,
        '>': cversion > rversion,
        '<': cversion < rversion
    }

    return res[s]


def get_results(deps_reqs):

    """
    :deps_reqs: list with packages from requirements files
    :return: sorted and compared packages list with state of condition
    """

    retlist = []
    retdict = {}

    for i in deps_reqs:

        # Get package_name, comparing symbol, version
        package_name, csymbol, version = parse_req_string(i)

        if package_name:

            retdict.update({
                package_name:
                    {
                        'current': version if version else 'latest',
                        'real': '',
                        'csymbol': csymbol
                    }
            })

    for item in retdict:
        current_version = retdict[item]['current']
        real_version = get_real_version(item)
        retdict[item]['real'] = real_version
        csymbol = retdict[item]['csymbol']
        if compare(current_version, real_version, csymbol):
            retlist.append('(+) {package}: current: {current} real: {real}'
                           .format(package=item,
                                   current=current_version,
                                   real=real_version))
        else:
            retlist.append('(-) {package}: current: {current} real: {real}'
                           .format(package=item,
                                   current=current_version,
                                   real=real_version))
    return sorted(retlist)


def find_file(configured_folder, file_path):

    if os.path.isfile(file_path):
        return file_path

    if os.path.isfile(os.path.join(configured_folder, file_path)):
        return os.path.join(configured_folder, file_path)

    return False


def open_file(file_path):

    """
    :file_path: path to files with requirements
    :return: list with requirements from target files and from related files
    """

    retlist = []

    dirname_file_path = os.path.dirname(file_path)

    with open(file_path, 'r') as tf:
        fi = tf.readlines()

    for i in fi:
        if i.startswith('-r'):
            found_path = \
                find_file(dirname_file_path, i.replace('-r', '').strip())

            if not found_path:
                print('File {} does not exist'.format(i))
                continue

            tlist = open_file(found_path)
            retlist.extend(tlist)
        else:
            tstr = i.strip()
            retlist.append(tstr)
    return retlist


def find_all_deps(list_file_path):

    """
    :list_file_path: path to file with requirements
    :return: all parsed files with requirements
    """

    temp_list = []
    for item_file in list_file_path:

        if not os.path.isfile(item_file):
            print('File {}  does not exist'.format(item_file))
            continue
        # Open files and create list of deps
        list_deps = open_file(item_file)
        temp_list.extend(list_deps)
    return list(set(temp_list))


def save_log(result_list, log_path):

    """
    :result_list: result list with compared package's versions
    :log_path: path for saving result_list
    :return: if everything is ok return log_path
    """

    if not os.path.isdir(os.path.dirname(log_path)):
        return "Path is unreachable"
    try:
        with open(log_path, 'w') as f:
            f.writelines('\n'.join(result_list))
    except OSError as e:
        return e
    return log_path


def main():

    """
    Main section
    """

    module = AnsibleModule(
        argument_spec=dict(
            dependencies=dict(required=True, type=list),
            log=dict(type=str)),
        supports_check_mode=True)
    params = module.params
    dependencies = params['dependencies']
    log = params['log']
    parsed_deps_lists = find_all_deps(dependencies)
    result_list = get_results(parsed_deps_lists)
    if log:
        save_log(result_list, log)
    module.exit_json(msg='Finished', text='\n' + '\n'.join(result_list))


if __name__ == '__main__':
    main()
