import os
import wget
import time
import json
import yaml
import zipfile
import platform
from getpass import getpass
from subprocess import Popen, PIPE, STDOUT
from json import JSONDecodeError
from onepassword.utils import read_bash_return, scrape, domain_from_email, Encryption, BashProfile
from onepassword.exceptions import OnePasswordForgottenPassword


class OnePassword:
    """
    Class for integrating with a One Password password manager

    :param install_only: Whether to just install the cli or not (optional, default=False)
    :type install_only: bool

    :param domain: domain of 1password account (optional, default=None)
    :type domain: str

    :param email: email address of 1password account (optional, default=None)
    :type email: str

    :param secret: secret key of 1password account (optional, default=None)
    :type secret: str

    :param password: password of 1password account (optional, default=None)
    :type password: str

    :param override_platform: name of the platform if already known (optional, default=None)
    :type override_platform: str

    :returns OnePassword: :obj:`instance`: OnePassword instance to allow code or user to manage credentials.

    """
    def __init__(self, install_only=False, domain=None, email=None, secret=None, password=None,
                 override_platform=None):  # pragma: no cover
        self.signin_domain = domain
        self.email_address = email
        self.secret_key = secret
        self.override_platform = override_platform
        if isinstance(override_platform, str):
            self.system = override_platform
        else:
            self.system = str(platform.system())
        self.user_home = read_bash_return("echo $HOME")
        # if self.system == "Linux":
        #     self.local_bin = os.path.join(self.user_home, ".local/bin/")
        # elif self.system == "Darwin":
        self.local_bin = "/usr/local/bin/"
        # Get most recent version
        self.sub_soup, self.link, self.version = self.get_link_version()
        self.major_version = self.version.split(".")[1]
        # Check if installed: if true, get update, if false install
        if self.check_cli():
            self.encrypted_master_password, self.session_key = self.signin_wrapper(master_password=password)
        else:
            self.install()
            if install_only:
                pass
            else:
                self.first_use(master_password=password)

    def get_link_version(self):
        """
        Helper function to get the most up to date link for downloading op cli

        :returns nt, download_link, version: :obj:`soup`, :obj:`str`, :obj:`str`: HTML soup, URL for download and the
            op cli version.

        """
        download_link = ""
        nt = scrape('https://app-updates.agilebits.com/product_history/CLI')
        n = nt.find("h3")
        version = n.decode_contents().split("<span")[0].split()[0]
        dl = nt.find("p", attrs={"class": "system {}".format(self.system.lower())})
        for d in dl.find_all("a"):
            if d.text == "amd64":
                download_link = d['href']
        return nt, download_link, version

    def check_cli(self):  # pragma: no cover
        """
        Helper function to check if op cli is already installed

        :returns: :obj:`bool`: True or False

         """
        if self.override_platform == self.system:
            return False
        else:
            op = read_bash_return("op --version")
            if op == "":
                return False
            elif op.split(".")[1] == self.major_version:
                return True
            else:
                return False

    def install(self):  # pragma: no cover
        """
        Helper function to download, unzip, install and chmod op cli files

        """
        op_file = self.link.split("/")[-1]
        if self.override_platform == self.system:
            download_path = os.path.join(self.user_home, op_file)
            final_path = self.user_home
        else:
            download_path = os.path.join(self.local_bin, op_file)
            final_path = self.local_bin
        # print('Downloading or updating the 1Password CLI: {}'.format(op_file))
        wget.download(self.link, download_path)
        if self.link[-4:] != ".pkg":
            zip_ref = zipfile.ZipFile(download_path, 'r')
            zip_ref.extractall(final_path)
            zip_ref.close()
            os.chmod(os.path.join(final_path, 'op'), 0o755)
            # print("Installed: {}".format(os.path.join(self.local_bin, op_file)))
        else:
            Popen(["open", os.path.join(self.local_bin, op_file)], stdin=PIPE, stdout=PIPE)  # pragma: no cover
            while self.check_cli():
                time.sleep(1)

    def first_use(self, master_password):  # pragma: no cover
        """
        Helper function to perform first time signin either with user interaction or not, depending on _init_
        :param master_password: password for 1password account (optional, default=None)
        :type master_password: str

        """
        # TODO: Could be wrapped into signin_wrapper()
        if master_password is None:
            email_address = input("Your email address for domain: ")
            signin_domain = domain_from_email(email_address)
            secret_key = getpass("1Password secret key: ")
            self.signin_wrapper(signin_domain, email_address, secret_key)
        else:
            self.signin_wrapper(self.signin_domain, self.email_address, self.secret_key)

    def signin_wrapper(self, domain=None, email=None, secret_key=None, master_password=None):  # pragma: no cover
        """
        Helper function for user to sign in but allows for three incorrect passwords. If successful signs in and updates
        bash profile, if not raises exception and points user to 1Password support.

        :param domain: domain of 1password account (optional, default=None)
        :type domain: str

        :param email: email address of 1password account (optional, default=None)
        :type email: str

        :param secret_key: secret key of 1password account (optional, default=None)
        :type secret_key: str

        :param master_password: password for 1password account (optional, default=None)
        :type master_password: str

        :return: encrypted_str, session_key - used by signin to know of existing login

        """
        global session_key
        global encrypted_str
        password, session_key, domain, bp = self.signin(domain, email, secret_key, master_password)
        tries = 1
        while tries < 3:
            if "(ERROR)  401" in session_key.decode():
                print("That's not the right password, try again.")
                password, session_key, domain, bp = self.signin(domain, email, secret_key, master_password)
                tries += 1
                pass
            else:
                os.environ["OP_SESSION_{}".format(domain)] = session_key.decode().replace("\n", "")
                bp.update_profile("OP_SESSION_{}".format(domain), session_key.decode().replace("\n", ""))
                encrypt = Encryption(session_key)
                encrypted_str = encrypt.encode(password)
                return encrypted_str, session_key
        raise OnePasswordForgottenPassword("You appear to have forgotten your password, visit: "
                                           "https://support.1password.com/forgot-master-password/")

    @staticmethod
    def signin(domain=None, email=None, secret_key=None, master_password=None):  # pragma: no cover
        """
        Helper function to prepare sign in for the user

        :param domain: domain of 1password account (optional, default=None)
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
        if master_password is not None:
            master_password = str.encode(master_password)
        else:
            if 'session_key' and 'encrypted_str' in globals():
                encrypt = Encryption(globals()['session_key'])
                master_password = str.encode(encrypt.decode(globals()['encrypted_str']))
            else:
                master_password = str.encode(getpass("1Password master password: "))
        if secret_key:
            process = Popen(['op', "signin", domain, email, secret_key, "--output=raw"], stdout=PIPE, stdin=PIPE,
                            stderr=STDOUT)
            # process.stdin.write(master_password)
            # session_key = process.communicate()[0]
            # process.stdin.close()
            # os.environ["OP_SESSION_{}".format(domain)] = session_key.decode().replace("\n", "")
            # bp.update_profile("OP_SESSION_{}".format(domain), session_key.decode().replace("\n", ""))
        else:
            if domain is None:
                try:
                    session_dict = bp.get_key_value("OP_SESSION", fuzzy=True)[0]  # list of dicts from BashProfile
                    domain = list(session_dict.keys())[0].split("OP_SESSION_")[1]
                except AttributeError:
                    domain = input("1Password signin domain e.g. wandera.1password.com = wandera: ")
                except ValueError:
                    raise ValueError("First signin failed or not executed.")
            process = Popen(['op', "signin", domain, "--output=raw"], stdout=PIPE, stdin=PIPE, stderr=STDOUT)

        process.stdin.write(master_password)
        sess_key = process.communicate()[0]
        process.stdin.close()
        return master_password, sess_key, domain, bp

    def get_uuid(self, docname, vault="Private"):  # pragma: no cover
        """
        Helper function to get the uuid for an item

        :param docname: title of the item (not filename of documents)
        :type docname: str

        :param vault: vault the item is in (optional, default=Private)
        :type vault: str

        :returns: uuid :obj:`str`: uuid of item or None if doesn't exist

        """
        items = self.get_items(vault=vault)
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
            return json.loads(read_bash_return("op get document {} --vault={}".format(docid, vault), single=False))
        except JSONDecodeError:
            yaml_attempt = yaml.safe_load(read_bash_return("op get document {} --vault={}".format(docid, vault),
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
        cmd = "op create document {} --title={} --vault={}".format(filename, title, vault)
        # [--tags=<tags>]
        response = read_bash_return(cmd)
        if len(response) == 0:
            self.signin()
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
        cmd = "op delete item {} --vault={}".format(docid, vault)
        response = read_bash_return(cmd)
        if len(response) > 0:
            self.signin()
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
        return read_bash_return('op signout')

    @staticmethod
    def list_vaults():
        """
        Helper function to list all vaults

        """
        return read_bash_return('op list vaults')

    @staticmethod
    def get_items(vault="Private"):
        """
        Helper function to get all items

        :param vault: vault the items are in (optional, default=Private)
        :type vault: str

        :returns: items :obj:`dict`: dict of all items

        """
        items = json.loads(read_bash_return("op list items --vault={}".format(vault)))
        return items
