# Check python package version

Module check python dependencies for updates using PyPi

## How to add module

Add module to directory 

```bash
library/check_python_package_version.py
```

## How to add to playbook

```yaml
- hosts: localhost
  connection: local
  tasks:
  - name: Check python deps
    check_python_package_version:
      dependencies: 
        - /test_requirements.txt
```
dependencies - set path to files with requiremnents list;

```bash
[+] django-admin-list-filter-dropdown: local: 1.0.1 latest: 1.0.1
[-] Django: local: 1.10.6 latest: 2.1.1
```
In square brackets:
[+] Local version and PyPi versions are equal.
[-] Local version and PyPi versiions are not equal.

