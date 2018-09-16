# Check python deps

Module check python dependencies for updates using PyPi

## How to add module

Add module to directory 

```bash
library/check_python_deps.py
```


## How to add to playbook

```yaml
- hosts: localhost
  connection: local
  tasks:
  - name: Check python deps
    check_python_deps:
      dependencies: 
        - /test_requirements.txt
      log: "{{ playbook_dir }}/log.txt"  
```

dependencies - set path to files with requiremnents list;
log - set path for log file which will be saved after excetion module;

Example of log file:

```bash
(+) certifi: current: latest real: 2018.8.24 
(+) django-admin-list-filter-dropdown: current: 1.0.1 real: 1.0.1
(-) Django: current: 1.10.6 real: 2.1.1
```

Plus and minus means that version satisfy or not requirements set in dependencies file; Current version - version
set in dependencies file,'latest' in curent version means that version has not been set in dependencies file; 
real version - version has been received in PyPi response.

P.S. Tips and tricks. For pretty print to stdout add -v parameter and sed to pipeline

Example

```bash
$ ansible-playbook you_playbook.yaml | sed 's/\\n/\n/g'
```
