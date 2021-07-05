# OnePassword python client
[![PyPi release](https://github.com/wandera/1password-client/actions/workflows/publish-to-pypi.yml/badge.svg?branch=main&event=push)](https://github.com/wandera/1password-client/actions/workflows/publish-to-pypi.yml)
[![CodeQL](https://github.com/wandera/1password-client/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/wandera/1password-client/actions/workflows/codeql-analysis.yml)

Python client around the 1Password password manager cli for usage within python code and
Jupyter Notebooks. Developed by Data Scientists from Wandera (a Jamf company).


## Installation
```bash
pip install 1password
```

If you have issues with PyYaml or other distutils installed packages then use:
```bash
pip install --ignore-installed 1password
```

You are welcome to install and manage `op` yourself by visiting 
https://support.1password.com/command-line-getting-started/

The above commands will check `op` is present already and if not will install the best `op` cli it can work out plus 
the python client itself. 
This is currently fixed at `op` version 1.10.3 to ensure compatibility. If you wish to use a higher version of `op` you
can by running `op update` in a terminal however note that we cannot ensure it will work with our client yet. 

Mac OS users will be prompted with a seperate installation windows to ensure you have a signed version of `op` - make
sure to check other desktops that the installer might pop up on. 

### Optional pre-requisites
#### base32
This utility is used to create a unique guid for your device but this isn't a hard requirement from AgileBits 
and so if you see `base32: command not found` an empty string will be used instead, 
and the client will still work fully.

If you really want to, you can make sure you have this installed by installing coreutils. Details per platform can
be found here: https://command-not-found.com/base32

## Basic Usage
Currently tested on Mac OS and Linux.

On first usage users will be asked for both the enrolled email, secret key and password. 
There is also verification of your account domain and name. 

For all following usages you will only be asked for a password.

You will be given 3 attempts and then pointed to reset password documentation or alternatively you can
restart your kernel.

No passwords are stored in memory without encryption.

If you have 2FA turned on for your 1Password account the client will ask for your six digit authenticator code.

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

### Input formats
To be sure what you are using is of the right format

- Enrolled email: standard email format e.g. user@example.com 
- Secret key: provided by 1Password e.g. ##-######-######-#####-#####-#####-#####
- Account domain: domain that you would login to 1Password via browser e.g. example.1password.com
- Account name: subdomain or account name that cli can use for multiple account holders e.g. example

## Contributing 
The GitHub action will run a full build, test and release on any push. 
If this is to the main branch then this will release to public PyPi and bump the patch version.

For a major or minor branch update your new branch should include this new version and this should be verified by the 
code owners.

In general, this means when contributing you should create a feature branch off of the main branch and without 
manually bumping the version you can focus on development.

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
- update: Check for and download updates

## Roadmap
- Add Windows functionality
- Add clean uninstall of client and op
- Remove subprocess usage everywhere -> use pexpect
- Add test docker image
- Get full UT coverage
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
