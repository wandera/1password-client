# OnePassword python client
[![Build Status](https://travis-ci.org/wandera/1password-client.svg?branch=master)](https://travis-ci.org/wandera/1password-client)

Python wrapper around 1Password password manager for usage within python scripts and
Jupyter Notebooks. Developed by Data Scientists from Wandera to be used within both 
research and python services use cases.


## Installation
```bash
pip install 1password
```


## Basic Usage
Currently fully tested on Mac OS.

On first usage users will be asked for both the enrolled email, secret key and master 
password. Mac OS users will also be prompted with installation windows to ensure you have the latest version of `op`.

For all following usages you will only be asked for a master password.

You will be given 3 attempts and then pointed to reset password documentation or alternatively you can
restart your kernel.

No passwords are stored in memory without encryption.

```python
from onepassword import OnePassword
import json

op = OnePassword()

# List all vaults 
json.loads(op.list_vaults())

# List all items in a vault, default is Private
op.list_items()

# Get all fields, one field or more fields for an item with uuid="example"
op.get_item(uuid="example")
op.get_item(uuid="example", fields="username")
op.get_item(uuid="example", fields=["username", "password"])

```


## Contributing 
The travis build will run with any PR or commit to master branch and then updates 
the master branch with a new minor version for contributors to branch from.

This means when contributing you should create a feature branch off of the master branch and without 
manually bumping the version can focus on development. Merge back into master.

Later admins will bump major versions.

## CLI coverage
Full op documentation can be found here: https://support.1password.com/command-line-reference/

The below is correct as of version 0.3.0.
### Commands
This is the set of commands the current python SDK covers:
- create: Create an object
    - document
- delete: Remove an object
    - item: we use this method to remove documents but now there is a new delete document method
- get: Get details about an object
    - document
    - item
- list: List objects and events
    - items
    - vaults
- signin: Sign in to a 1Password account
- signout: Sign out of a 1Password account


This is what still needs developing due to new functionality being released:
- add: Grant access to groups or vaults
    - group 
    - user
- completion: Generate shell completion information
- confirm: Confirm a user
- create: Create an object
    - group
    - user
    - item
    - vault 
- delete: Remove an object
    - document
    - user
    - vault
    - group
    - trash
- edit: Edit an object
    - document
    - group
    - item
    - user
    - vault
- encode: Encode the JSON needed to create an item
- forget: Remove a 1Password account from this device
- get: Get details about an object
    - account
    - group
    - template
    - totp
    - user
    - vault
- list: List objects and events
    - documents
    - events
    - groups
    - templates
    - users
- reactivate: Reactivate a suspended user
- remove: Revoke access to groups or vaults
- suspend: Suspend a user
- update: Check for and download updates - we have some custom code for this but now is covered by CLI

## Roadmap
- Fix and test Linux implementation
- Add UTs
- Add test docker image
- Align response types into JSON / lists instead of JSON strings
- Ensure full and matching functionality of CLI in python
    - add
    - confirm
    - create
    - delete
    - edit
    - encode
    - forget
    - get
    - list
    - reactivate
    - remove
    - suspend
- Use the new CLI update method
