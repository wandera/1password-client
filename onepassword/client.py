import os
import json
import platform
import yaml
import subprocess
from subprocess import CompletedProcess
from typing import Any
from getpass import getpass
from json import JSONDecodeError
from onepassword.utils import read_bash_return, domain_from_email, Encryption, BashProfile, get_device_uuid, \
    _spawn_signin
from onepassword.exceptions import OnePasswordForgottenPassword

SERVICE_ACCOUNT_TOKEN = "OP_SERVICE_ACCOUNT_TOKEN"


class SignIn:
    """
    Helper class for methods common between App and Manual sign in
    """
    _env_account = "OP_ACCOUNT"

    def get_account(self, bash_profile: BashProfile | None = None) -> str:
        """
        Get the 1Password account name, using either the stored name or inputs

        :param bash_profile: Stored bash profile. (Optional, default = None)
        :return: 1Password account name
        """
        if bash_profile is None:
            return self._input_account()
        else:
            return self._get_account_bash(bash_profile)

    @staticmethod
    def _input_account() -> str:
        account = input("Please input your 1Password personal or business acount name e.g. company from "
                        "company.1password.com: ")
        return account

    def _get_account_bash(self, bash_profile: BashProfile) -> str:
        try:
            session_dict = bash_profile.get_key_value(self._env_account, fuzzy=True)[0]
            account = session_dict.get("OP_ACCOUNT").strip('\"')
        except AttributeError:
            account = self._input_account()
        except ValueError:
            raise ValueError("First signin failed or not executed.")
        return account

    @staticmethod
    def get_domain() -> str:
        """
        Get the domain name for the 1Password account

        :return: 1Password domain name
        """
        domain = input("Please input your 1Password domain in the format <something>.1password.com: ")
        return domain

    def _update_bash_account(self, account: str, bash_profile: BashProfile) -> None:
        os.environ[self._env_account] = account
        bash_profile.update_profile(self._env_account, account)

    def signin(self):
        pass


class ManualSignIn(SignIn):
    """
    Class to sign in to 1Password manually, see: https://developer.1password.com/docs/cli/sign-in-manually

    :param account: Shorthand account name for your 1Password account e.g. wandera from wandera.1password.com.
        (Optional, default = None)
    :param password: 1Password password. (Optional, default = None)
    """

    _env_session = "OP_SESSION"

    def __init__(self, account: str | None = None, password: str | None = None) -> None:
        # pragma: no cover
        bp = BashProfile()
        os.environ["OP_DEVICE"] = get_device_uuid(bp)
        # reuse existing op session
        if isinstance(account, str) and "{}_{}".format(self._env_account, account) in os.environ:
            pass
        # Check first time: if true, full signin, else use shortened signin
        elif self._check_not_first_time(bp):
            self.encrypted_master_password, self.session_key = self.signin_wrapper(
                account=account,
                master_password=password
            )
        else:
            self.first_use()

    def _check_not_first_time(self, bp: BashProfile) -> bool:
        for line in bp.profile_lines:
            if self._env_session in line:
                return True
            return False

    def first_use(self):  # pragma: no cover
        """
        Helper function to perform first time signin either with user interaction or not, depending on _init_
        """
        email_address = input("Please input your email address used for 1Password account: ")
        account = domain_from_email(email_address)
        signin_domain = account + ".1password.com"
        confirm_signin_domain = input("Is your 1Password domain: {} (y/n)? ".format(signin_domain))
        if confirm_signin_domain == "y":
            pass
        else:
            signin_domain = self.get_domain()

        confirm_account = input("Is your 1Password account name: {} (y/n)? ".format(account))
        if confirm_account == "y":
            pass
        else:
            account = self.get_account()
        secret_key = getpass("Please input your 1Password secret key: ")
        self.signin_wrapper(account, signin_domain, email_address, secret_key)

    def signin_wrapper(
            self, account: str | None = None, domain: str | None = None, email: str | None = None,
            secret_key: str | None = None, master_password: str | None = None
    ) -> tuple[str, str]:
        # pragma: no cover
        """
        Helper function for user to sign in but allows for three incorrect passwords. If successful signs in and updates
        bash profile, if not raises exception and points user to 1Password support.

        :param account: Shorthand account name for your 1Password account e.g. wandera from wandera.1password.com.
            (Optional, default = None)
        :param domain: Full domain name of 1Password account e.g. wandera.1password.com (Optional, default=None)
        :param email: Email address of 1Password account (Optional, default=None)
        :param secret_key: Secret key of 1Password account (Optional, default=None)
        :param master_password: Password for 1Password account (Optional, default=None)
        :return: encrypted_str, session_key - used by signin to know of existing login
        """

        password, session_key, domain, account, bp = self.signin(account, domain, email, secret_key, master_password)
        tries = 1
        while tries < 3:
            if session_key is False:  # Not the right password, trying again
                password, session_key, domain, account, bp = self.signin(
                    account, domain, email, secret_key, master_password)
                tries += 1
                pass
            else:
                self._update_bash_account(account, bp)
                os.environ["{}_{}".format(self._env_session, account)] = session_key.replace("\n", "")
                bp.update_profile("{}_{}".format(self._env_session, account), session_key.replace("\n", ""))
                encrypt = Encryption(session_key)
                encrypted_str = encrypt.encode(password)
                return encrypted_str, session_key
        raise OnePasswordForgottenPassword("You appear to have forgotten your password, visit: "
                                           "https://support.1password.com/forgot-master-password/")

    def signin(
            self, account: str | None = None, domain: str | None = None, email: str | None = None,
            secret_key: str | None = None, master_password: str | None = None
    ) -> tuple[bytes | None, str | bool, str | None, str | None | Any, BashProfile]:  # pragma: no cover
        """
        Helper function to prepare sign in for the user

        :param account: Shorthand name for your 1Password account e.g. wandera from wandera.1password.com
            (Optional, default=None)
        :param domain: Full domain name of 1Password account e.g. wandera.1password.com (Optional, default=None)
        :param email: Email address of 1Password account (Optional, default=None)
        :param secret_key: Secret key of 1Password account (Optional, default=None)
        :param master_password: Password for 1Password account (Optional, default=None)
        :return: master_password, sess_key, domain, bp - all used by wrapper
        """
        bp = BashProfile()
        op_command = ""
        if master_password is not None:
            master_password = str.encode(master_password)
        else:
            if 'op' in locals():
                initiated_class = locals()["op"]
                if 'session_key' and 'encrypted_master_password' in initiated_class.__dict__:
                    encrypt = Encryption(initiated_class.session_key)
                    master_password = str.encode(encrypt.decode(initiated_class.encrypted_master_password))
            else:
                master_password = str.encode(getpass("Please input your 1Password master password: "))
        if secret_key:
            op_command = "op account add --address {} --email {} --secret-key {} --shorthand {} --signin --raw".format(
                domain, email, secret_key, account)
        else:
            if account is None:
                try:
                    session_dict = bp.get_key_value(self._env_session, fuzzy=True)[0]  # list of dicts from BashProfile
                    account = list(session_dict.keys())[0].split(self._env_session + "_")[1]
                except AttributeError:
                    account = input("Please input your 1Password account name e.g. wandera from "
                                    "wandera.1password.com: ")
                except ValueError:
                    raise ValueError("First signin failed or not executed.")

            op_command = "op signin --account {} --raw".format(account)
        sess_key = _spawn_signin(op_command, master_password)
        return master_password, sess_key, domain, account, bp


class AppSignIn(SignIn):
    """
    Class to sign in to 1Password using the 1Password app integration,
    see: https://developer.1password.com/docs/cli/app-integration

    :param account: Shorthand account name for your 1Password account e.g. wandera from wandera.1password.com.
        (Optional, default = None)
    """
    def __init__(self, account: str | None = None) -> None:
        self.signin(account)

    @staticmethod
    def _do_signin(account: str) -> CompletedProcess[Any] | CompletedProcess[str]:
        return subprocess.run("op signin --account {}".format(account), shell=True, capture_output=True, text=True)

    @staticmethod
    def _do_open_app(default_error: str) -> CompletedProcess[Any] | CompletedProcess[str]:
        if platform.system() == "Darwin":
            return subprocess.run("open -a 1Password.app", shell=True)
        elif platform.system() == "Linux":
            return subprocess.run("1password", shell=True)
        else:
            raise ConnectionError(default_error)

    def _signin_wrapper(self, account: str) -> None:
        r = self._do_signin(account)
        if r.returncode != 0:
            if "please unlock it in the 1Password app" in r.stderr:
                open_app = self._do_open_app(r.stderr.rstrip("\n"))
                if open_app.returncode == 0:
                    sign_in = self._do_signin(account)
                    if sign_in.returncode != 0:
                        raise ConnectionError(sign_in.stderr.rstrip("\n"))
                else:
                    raise ConnectionError(r.stderr.rstrip("\n"))
            raise ConnectionError(r.stderr.rstrip("\n"))

    def signin(self, account: str | None = None) -> None:
        """
        Sign in to your 1Password account using the app integration

        :param account: Shorthand account name for your 1Password account e.g. wandera from wandera.1password.com.
        (Optional, default = None)
        """
        bash_profile = BashProfile()
        if account is None:
            account = self.get_account(bash_profile)
        self._signin_wrapper(account)
        self._update_bash_account(account, bash_profile)


class ServiceSignIn(SignIn):
    def __init__(self):
        self.signin()

    def signin(self):
        if os.environ['OP_SERVICE_ACCOUNT_TOKEN'] != "":
            print("Using service account, for supported commands see: "
                  "https://developer.1password.com/docs/service-accounts/use-with-1password-cli#supported-commands")
            self.account_details = yaml.safe_load(read_bash_return("op user get --me", single=False))
            self.account = self.account_details["Name"]
        else:
            print("No service account found, please setup on the web version of 1Password for more information go here:"
                  " https://developer.1password.com/docs/service-accounts/use-with-1password-cli")



class OnePassword:
    """
    Class for integrating with a OnePassword password manager

    :param signin_method: Sign in method for 1Password (Optional, default = 'app', options: 'app', 'manual')
    :param account: 1Password account name (Optional, default=None)
    :param password: password of 1Password account (Optional, default=None)
    """
    def __init__(self, signin_method: str = "app", account: str | None = None, password: str | None = None) -> None:
        # pragma: no cover
        if SERVICE_ACCOUNT_TOKEN in os.environ.keys():
            self.signin_strategy = ServiceSignIn()
        else:
            if signin_method == "app":
                self.signin_strategy = AppSignIn(account)
            elif signin_method == "manual":
                self.signin_strategy = ManualSignIn(account, password)
            else:
                raise ValueError("Unrecognised 'signin_method', options are: 'app' or 'manual'. "
                                 "See: https://developer.1password.com/docs/cli/verify")

    def get_uuid(self, docname: str, vault: str = "Private") -> str:  # pragma: no cover
        """
        Helper function to get the uuid for an item

        :param docname: Title of the item (not filename of documents)
        :param vault: Vault the item is in (Optional, default=Private)
        :return: Uuid of item or None if it doesn't exist
        """
        items = self.list_items(vault=vault)
        for t in items:
            if t["title"] == docname:
                return t["id"]

    def get_document(self, docname: str, vault: str = "Private") -> dict | None:  # pragma: no cover
        """
        Helper function to get a document

        :param docname: Title of the document (not it's filename)
        :param vault: Vault the document is in (Optional, default=Private)
        :returns: Document or None if it doesn't exist

        """
        document_str = self.get_document_str(docname, vault)
        if isinstance(document_str, str):
            try:
                return json.loads(document_str)
            except JSONDecodeError:
                yaml_attempt = yaml.safe_load(document_str)
                if isinstance(yaml_attempt, dict):
                    return yaml_attempt
                else:
                    print("File {} does not exist in 1Password vault: {}".format(docname, vault))
                    return None
        else:
            return None

    def get_document_str(self, docname: str, vault: str = "Private") -> str | None:  # pragma: no cover
        """
        Helper function to get a document

        :param docname: Title of the document (not it's filename)
        :param vault: Vault the document is in (Optional, default=Private)

        :returns: Document or None is non existant
        :rtype: str | None

        """
        docid = self.get_uuid(docname, vault=vault)
        document = None
        if isinstance(docid, str):
            document = read_bash_return("op document get {} --vault='{}'".format(docid, vault), single=False)
        return document

    def put_document(self, filename: str, title: str, vault: str = "Private") -> None:  # pragma: no cover
        """
        Helper function to put a document

        :param filename: Path and filename of document (must be saved locally already)
        :param title: Title you wish to call the document
        :param vault: Vault the document is in (Optional, default=Private)
        """
        cmd = "op document create {} --title={} --vault='{}'".format(filename, title, vault)
        # [--tags=<tags>]
        response = read_bash_return(cmd)
        if len(response) == 0:
            self.signin_strategy.signin()
            read_bash_return(cmd)
            # self.signout()
        # else:
        # self.signout()

    def delete_document(self, title: str, vault: str = "Private") -> None:  # pragma: no cover
        """
        Helper function to delete a document

        :param title: Title of the document you wish to remove
        :param vault: Vault the document is in (Optional, default=Private)
        """
        docid = self.get_uuid(title, vault=vault)
        cmd = "op item delete {} --vault='{}'".format(docid, vault)
        response = read_bash_return(cmd)
        if len(response) > 0:
            self.signin_strategy.signin()
            read_bash_return(cmd)
            # self.signout()
        # else:
        # self.signout()

    def update_document(self, filename: str, title: str, vault: str = 'Private') -> None:  # pragma: no cover
        """
        Helper function to update an existing document in 1Password.

        :param title: Name of the document in 1Password.
        :param filename: Path and filename of document (must be saved locally already).
        :param vault: Vault the document is in (Optional, default=Private).
        """

        # delete the old document
        self.delete_document(title, vault=vault)

        # put the new updated one
        self.put_document(filename, title, vault=vault)

        # remove the saved file locally
        os.remove(filename)

    @staticmethod
    def signout():
        """
        Helper function to sign out of 1Password
        """
        read_bash_return("op signout")

    @staticmethod
    def list_vaults():
        """
        Helper function to list all vaults
        """
        return json.loads(read_bash_return("op vault list --format=json", single=False))

    @staticmethod
    def list_items(vault: str = "Private") -> dict:
        """
        Helper function to list all items in a certain vault

        :param vault: Vault the items are in (Optional, default=Private)
        :returns: Dictionary of all items
        """
        items = json.loads(read_bash_return("op items list --vault='{}' --format=json".format(vault), single=False))
        return items

    @staticmethod
    def get_item(uuid: str | bytes, fields: str | bytes | list | None = None, vault: str | bytes | None = None):
        """
        Helper function to get a certain field, you can find the UUID you need using list_items

        :param uuid: Uuid of the item you wish to get, no vault needed
        :param fields: To return only certain detail use either a specific field or list of them
            (Optional, default=None which means all fields returned)
        :param vault: When using service account, a vault must be provided. A vault may be specified by name or ID.
        :return: Dictionary of the item with requested fields
        """
        vault_flag = f"--vault {vault}" if vault else ""
        if isinstance(fields, list):
            item_list = json.loads(read_bash_return(
                "op item get {} --format=json --fields label={} {}".format(uuid, ",label=".join(fields), vault_flag),
                single=False))
            item = {}
            if isinstance(item_list, dict):
                item[fields[0]] = item_list["value"]
            else:
                for i in item_list:
                    item[i["id"]] = i["value"]
        elif isinstance(fields, str):
            item = {
                fields: read_bash_return(
                    "op item get {} --fields label={} {}".format(uuid, fields, vault_flag), single=False).rstrip('\n')
            }
        else:
            item = json.loads(read_bash_return("op item get {} --format=json {}".format(uuid, vault_flag), single=False))
        return item

    @staticmethod
    def read(secret_ref: str):
        """
        Helper function to read a secret based on its reference(ex: op://<vault>/<item>/<field>)
        You can get this reference from the UI or by using this command:
        op item get <item> --format json --fields <secret_field>

        :param secret_ref: Reference to the secret you wish to read
        :return: The secret in plain text
        """
        if not secret_ref or not isinstance(secret_ref, str):
            raise ValueError("secret_ref must be a non-empty string")

        return read_bash_return("op read '{}'".format(secret_ref))

    @staticmethod
    def get_item_otp(uuid: str | bytes):
        """
        Helper function to get the item otp, you can find the UUID you need using list_items

        :param uuid: Uuid of the item you wish to get, no vault needed
        :return: the otp of the item, if it exists
        """
        return read_bash_return("op item get {} --otp".format(uuid), single=False).rstrip('\n')

