# OnePassword python client
[![PyPi release](https://github.com/wandera/1password-client/actions/workflows/publish-to-pypi.yml/badge.svg?branch=main&event=push)](https://github.com/wandera/1password-client/actions/workflows/publish-to-pypi.yml)
[![CodeQL](https://github.com/wandera/1password-client/actions/workflows/codeql-analysis.yml/badge.svg)](https://github.com/wandera/1password-client/actions/workflows/codeql-analysis.yml)

Python client around the 1Password password manager cli for usage within python code and
Jupyter Notebooks. Developed by Data Scientists from Jamf.

## Supported versions
There are some of the pre-requisites that are needed to use the library. We automatically install the cli for Mac and
Linux users when installing the library. Windows users see below for help.

- 1Password App: 8+
- 1Password cli: 2+
- Python: 3.10+

## Operating systems
The library is split into two parts: installation and client in which we are slowly updating to cover as many operating
systems as possible the following table should ensure users understand what this library can and can't do at time of 
install.

|                  | MacOS | Linux | 
|------------------|-------|-------|
| Fully supported  | Y     | Y     | 
| CLI install      | Y     | Y     | 
| SSO login        | Y     | Y     | 
| Login via App    | Y     | Y     | 
| Biometrics auth  | Y     | Y     | 
| Password auth    | Y     | Y     | 
| CLI client       | Y     | Y     | 
| Service account  | Y     | Y     |

## Installation
```bash
pip install 1password
```

If you have issues with PyYaml or other distutils installed packages then use:
```bash
pip install --ignore-installed 1password
```

You are welcome to install and manage `op` yourself by visiting
[the CLI1 downloads page](https://app-updates.agilebits.com/product_history/CLI ) to download the version you require 
and follow instructions for your platform as long as it's major version 2.

The above commands pip commands will check `op` is present already and if not will install the supported `op` cli 
plus the python client itself. 
This is currently fixed at `op` version 1.12.5 to ensure compatibility. If you wish to use a higher version of `op` you
can by following [this guide](https://developer.1password.com/docs/cli/upgrade), 
however note that we cannot ensure it will work with our client yet. 

MacOS users will be prompted with a separate installation window to ensure you have a signed version of `op` - make
sure to check other desktops that the installer might pop up on. 


### Optional pre-requisites
#### base32
This utility is used to create a unique guid for your device but this isn't a hard requirement from AgileBits 
and so if you see `base32: command not found` an empty string will be used instead, 
and the client will still work fully.

If you really want to, you can make sure you have this installed by installing coreutils. Details per platform can
be found here: https://command-not-found.com/base32

## Basic Usage
Since v2 of the cli it is advised to connect your CLI to the local app installed on the device, thus removing the need
for secret keys and passwords in the terminal or shell. Read here on how to do that: 
https://developer.1password.com/docs/cli/get-started#step-2-turn-on-the-1password-desktop-app-integration

An added extra for Mac users is that you can also enable TouchID for the app and by linking your cli with the app you 
will get biometric login for both. 

Once this is done any initial usage of the cli, and our client will request you to authenticate either via the app or 
using your biometrics and then you can continue.

We are sure there are use cases where the app cannot be linked and hence a password etc is till required so this 
functionality is still present from our v1 implementation and can be described below

### Password authentication
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
### Service Accounts
We also support authentication using Service accounts, however these are not interchangeable with other auth routes and 
hence other accounts i.e. this token based authentication will take precedence over any other method. 
If you wish to use multiple account types, for now you will need to design this workflow yourself
by clearing out the OP_SERVICE_ACCOUNT_TOKEN using `unset OP_SERVICE_ACCOUNT_TOKEN` before re-authenticating with 
your preferred account. 

To use a service account make sure to fulfil the requirements here: 
https://developer.1password.com/docs/service-accounts/use-with-1password-cli
and note that not all of the CLI commands are supported at this time. 

Also note that your service account will only have access to certain vaults. In particular it will not be able to see 
the `Shared` or `Private` vaults in any account. In our client this means you must always use the `vault` option, e.g. like so:

```python
from onepassword import OnePassword

op = OnePassword()
op.get_item(uuid="example_item", vault="example_vault")
```

Once you have fulfilled all the requirements, namely `export OP_SERVICE_ACCOUNT_TOKEN=<your token>`, you can then use 
our client with:

```python
from onepassword import OnePassword

op = OnePassword()
op.list_vaults()
```

### Secret References

Secret references are direct keys to a field in an item. They are useful when trying to get only one field(ex. API Key or a password) from an item.

You can fetch secret based on secret references with the following code:

```python
from onepassword import OnePassword

op = OnePassword()
op.read("op://<vault>/<item>/<field>")
```

You can get the secret reference in one of the supported ways explained here:
https://developer.1password.com/docs/cli/secret-references/

Or you can use this:
```python
from onepassword import OnePassword

op = OnePassword()
op.get_item("Item")["fields"][0]['reference']
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
- read: Get a secret based on a secret reference
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
