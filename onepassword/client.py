import os
import json
import yaml
from getpass import getpass
from json import JSONDecodeError
from onepassword.utils import read_bash_return, domain_from_email, Encryption, BashProfile, get_device_uuid, \
    _spawn_signin
from onepassword.exceptions import OnePasswordForgottenPassword


class OnePassword:
    """
    Class for integrating with a One Password password manager

    :param domain: domain of 1password account (optional, default=None)
    :type domain: str

    :param email: email address of 1password account (optional, default=None)
    :type email: str

    :param secret: secret key of 1password account (optional, default=None)
    :type secret: str

    :param password: password of 1password account (optional, default=None)
    :type password: str

    :returns OnePassword: :obj:`instance`: OnePassword instance to allow code or user to manage credentials.

    """
    def __init__(self, account=None, domain=None, email=None, secret=None, password=None):  # pragma: no cover
        self.signin_domain = domain
        self.email_address = email
        self.secret_key = secret
        bp = BashProfile()
        os.environ["OP_DEVICE"] = get_device_uuid(bp)
        # reuse existing op session
        if isinstance(account, str) and "OP_SESSION_{}".format(account) in os.environ:
            pass
        # Check first time: if true, full signin, else use shortened signin
        elif self.check_not_first_time(bp):
            self.encrypted_master_password, self.session_key = self.signin_wrapper(account=account,
                                                                                   master_password=password)
        else:
            self.first_use()

    @staticmethod
    def check_not_first_time(bp):
        line_checks = []
        for line in bp.profile_lines:
            if "OP_SESSION" in line:
                line_checks.append(True)
            else:
                line_checks.append(False)
        return any(line_checks)

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
            signin_domain = input("Please input your 1Password domain in the format <something>.1password.com: ")

        confirm_account = input("Is your 1Password account name: {} (y/n)? ".format(account))
        if confirm_account == "y":
            pass
        else:
            account = input("Please input your 1Password account name e.g. wandera from wandera.1password.com: ")
        secret_key = getpass("Please input your 1Password secret key: ")
        self.signin_wrapper(account, signin_domain, email_address, secret_key)

    def signin_wrapper(self, account=None, domain=None, email=None, secret_key=None, master_password=None):
        # pragma: no cover
        """
        Helper function for user to sign in but allows for three incorrect passwords. If successful signs in and updates
        bash profile, if not raises exception and points user to 1Password support.

        :param account: shorthand name for your 1password account e.g. wandera from wandera.1password.com (optional,
        default=None)

        :param domain: full domain name of 1password account e.g. wandera.1password.com (optional, default=None)
        :type domain: str

        :param email: email address of 1password account (optional, default=None)
        :type email: str

        :param secret_key: secret key of 1password account (optional, default=None)
        :type secret_key: str

        :param master_password: password for 1password account (optional, default=None)
        :type master_password: str

        :return: encrypted_str, session_key - used by signin to know of existing login

        """

        password, session_key, domain, account, bp = self._signin(account, domain, email, secret_key, master_password)
        tries = 1
        while tries < 3:
            if "(ERROR)  401" in session_key:
                print("That's not the right password, try again.")
                password, session_key, domain, account, bp = self._signin(account, domain, email, secret_key,
                                                                          master_password)
                tries += 1
                pass
            else:
                # device_uuid = generate_uuid()
                os.environ["OP_SESSION_{}".format(account)] = session_key.replace("\n", "")
                # os.environ["OP_DEVICE"] = device_uuid
                bp.update_profile("OP_SESSION_{}".format(account), session_key.replace("\n", ""))
                # bp.update_profile("OP_DEVICE", device_uuid)
                encrypt = Encryption(session_key)
                encrypted_str = encrypt.encode(password)
                return encrypted_str, session_key
        raise OnePasswordForgottenPassword("You appear to have forgotten your password, visit: "
                                           "https://support.1password.com/forgot-master-password/")

    @staticmethod
    def _signin(account=None, domain=None, email=None, secret_key=None, master_password=None):  # pragma: no cover
        """
        Helper function to prepare sign in for the user

        :param account: shorthand name for your 1password account e.g. wandera from wandera.1password.com (optional,
        default=None)

        :param domain: full domain name of 1password account e.g. wandera.1password.com (optional, default=None)
        :type domain: str

        :param email: email address of 1password account (optional, default=None)
        :type email: str

        :param secret_key: secret key of 1password account (optional, default=None)
        :type secret_key: str

        :param master_password: password for 1password account (optional, default=None)
        :type master_password: str

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
            op_command = "op signin {} {} {} --raw --shorthand {}".format(domain, email, secret_key, account)
        else:
            if account is None:
                try:
                    session_dict = bp.get_key_value("OP_SESSION", fuzzy=True)[0]  # list of dicts from BashProfile
                    account = list(session_dict.keys())[0].split("OP_SESSION_")[1]
                except AttributeError:
                    account = input("Please input your 1Password account name e.g. wandera from "
                                    "wandera.1password.com: ")
                except ValueError:
                    raise ValueError("First signin failed or not executed.")
            op_command = "op signin {} --raw".format(account)
        sess_key = _spawn_signin(op_command, master_password)
        return master_password, sess_key, domain, account, bp

    def get_uuid(self, docname, vault="Private"):  # pragma: no cover
        """
        Helper function to get the uuid for an item

        :param docname: title of the item (not filename of documents)
        :type docname: str

        :param vault: vault the item is in (optional, default=Private)
        :type vault: str

        :returns: uuid :obj:`str`: uuid of item or None if doesn't exist

        """
        items = self.list_items(vault=vault)
        for t in items:
            if t['overview']['title'] == docname:
                return t['uuid']

    def get_document(self, docname, vault="Private"):  # pragma: no cover
        """
        Helper function to get a document

        :param docname: title of the document (not it's filename)
        :type docname: str

        :param vault: vault the document is in (optional, default=Private)
        :type vault: str

        :returns: :obj:`dict`: document or None if doesn't exist

        """
        docid = self.get_uuid(docname, vault=vault)
        try:
            return json.loads(read_bash_return("op get document {} --vault='{}'".format(docid, vault), single=False))
        except JSONDecodeError:
            yaml_attempt = yaml.safe_load(read_bash_return("op get document {} --vault='{}'".format(docid, vault),
                                                           single=False))
            if isinstance(yaml_attempt, dict):
                return yaml_attempt
            else:
                print("File {} does not exist in 1Password vault: {}".format(docname, vault))
                return None

    def put_document(self, filename, title, vault="Private"):  # pragma: no cover
        """
        Helper function to put a document

        :param filename: path and filename of document (must be saved locally already)
        :type filename: str

        :param title: title you wish to call the document
        :type title: str

        :param vault: vault the document is in (optional, default=Private)
        :type vault: str

        """
        cmd = "op create document {} --title={} --vault='{}'".format(filename, title, vault)
        # [--tags=<tags>]
        response = read_bash_return(cmd)
        if len(response) == 0:
            self._signin()
            read_bash_return(cmd)
            # self.signout()
        # else:
        # self.signout()

    def delete_document(self, title, vault="Private"):  # pragma: no cover
        """
        Helper function to delete a document

        :param title: title of the document you wish to remove
        :type title: str

        :param vault: vault the document is in (optional, default=Private)
        :type vault: str

        """
        docid = self.get_uuid(title, vault=vault)
        cmd = "op delete item {} --vault='{}'".format(docid, vault)
        response = read_bash_return(cmd)
        if len(response) > 0:
            self._signin()
            read_bash_return(cmd)
            # self.signout()
        # else:
        # self.signout()

    def update_document(self, filename, title, vault='Private'):  # pragma: no cover
        """
        Helper function to update an existing document in 1Password.

        :param title: name of the document in 1Password.
        :type title: str

        :param filename: path and filename of document (must be saved locally already).
        :type: filename: str

        :param vault: vault the document is in (optional, default=Private).
        :type vault: str

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
        Helper function to sign out of 1pass

        """
        read_bash_return('op signout')

    @staticmethod
    def list_vaults():
        """
        Helper function to list all vaults

        """
        return read_bash_return('op list vaults')

    @staticmethod
    def list_items(vault="Private"):
        """
        Helper function to list all items in a certain vault

        :param vault: vault the items are in (optional, default=Private)
        :type vault: str

        :returns: items :obj:`dict`: dict of all items

        """
        items = json.loads(read_bash_return("op list items --vault='{}'".format(vault)))
        return items

    @staticmethod
    def get_item(uuid, fields=None):
        """
        Helper function to get a certain field, you can find the UUID you need using list_items

        :param uuid: uuid of the item you wish to get, no vault needed
        :type uuid: str or bytes

        :param fields: to return only certain detail use either a specific field or list of them
        (optional, default=None which means all fields returned)
        :type fields: str or bytes or list

        :return: item :obj: `dict`: dict of the item with requested fields

        """
        if isinstance(fields, list):
            item = json.loads(read_bash_return("op get item {} --fields {}".format(uuid, ",".join(fields))))
        elif isinstance(fields, str):
            item = {fields: read_bash_return("op get item {} --fields {}".format(uuid, fields))}
        else:
            item = json.loads(read_bash_return("op get item {}".format(uuid)))
        return item
