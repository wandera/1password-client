import os
import base64
from bs4 import BeautifulSoup
from Crypto.Cipher import AES
from urllib.request import urlopen, Request


def read_bash_return(cmd, single=True):
    process = os.popen(cmd)
    preprocessed = process.read()
    process.close()
    if single:
        return str(preprocessed.split("\n")[0])
    else:
        return str(preprocessed)


def docker_check():
    f = None
    user_home = os.environ.get('HOME')
    for rcfile in ['.bashrc', '.bash_profile', '.zshrc', '.zprofile']:
        rcpath = os.path.join(user_home, rcfile)
        if os.path.exists(rcpath):
            f = open(os.path.join(user_home, rcpath), "r")
            break
    if not f:
        raise Exception("No sehll rc or profile files exist.")
    bash_profile = f.read()
    try:
        docker_flag = bash_profile.split('DOCKER_FLAG="')[1][0]
        if docker_flag == "t":
            return True
        else:
            return False
    except IndexError:
        return False


def scrape(webpage, initial_tag=None, initial_attrs=None, headers=None):
    """
    Function to scrape a web page

    :param webpage: web page you wish to scrape
    :type webpage: str

    :param initial_tag: if you want to find a particular sub element of the HTML enter the
        parent tag here (optional)
    :type initial_tag: str

    :param initial_attrs: for multiple parent tags you may want a certain set of attributes
        to enhance the search, input those here (optional)
    :type initial_attrs: dict

    :param headers:  :obj:`dict`: headers to use to make request to page

    :return: soup or tag / sub element
    """
    if headers is None:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 '
                          'Safari/537.3'
        }
    req = Request(url=webpage, headers=headers)
    page = urlopen(req)
    soup = BeautifulSoup(page, 'html.parser')
    if initial_tag is None:
        return soup
    else:
        sub_element = soup.find(initial_tag, attrs=initial_attrs)
        return sub_element


def domain_from_email(address):
    """
    Method to extract a domain without sld or tld from an email address

    :param address: email address to extract from
    :type address: str

    :return: domain (str)
    """
    return address.split("@")[1].split(".")[0]


class BashProfile:
    def __init__(self):
        f = None
        user_home = os.environ.get('HOME')
        for rcfile in ['.bashrc', '.bash_profile', '.zshrc', '.zprofile']:
            rcpath = os.path.join(user_home, rcfile)
            if os.path.exists(rcpath):
                f = open(os.path.join(user_home, rcpath), "r")
                break
        if not f:
            raise Exception("No shell rc or profile files exist.")
        self.other_profile_flag = False
        if docker_check():
            f2 = None
            try:
                f2 = open(os.path.join(user_home, ".profile"), "r")
            except IOError:
                print("Profile file does not exist.")
            self.other_profile = f2.read()
            self.other_profile_filename = f2.name
            self.other_profile_flag = True
            self.other_profile_lines = f2.readlines()
            f2.close()
        self.profile_lines = f.readlines()
        self.profile = f.read()
        self.profile_filename = f.name
        f.close()

    def get_key_value(self, key, fuzzy=False):
        key_lines = self.get_key_line(key, fuzzy=fuzzy)
        if key_lines:
            key_values = []
            for ky in key_lines:
                k = ky.split("=")[0].split(" ")[1]
                v = ky.split("=")[1]
                key_values.append({k: v})
            return key_values
        else:
            raise ValueError("Environment variable does not exist.")

    def get_key_line(self, key, fuzzy=False):
        key_line = None
        if self.other_profile_flag:
            prof = [self.other_profile_lines, self.profile_lines]
        else:
            prof = [self.profile_lines]

        key_lines = []
        for prof_lines in prof:
            if len(prof_lines) > 0:
                for p in prof_lines:
                    if (~fuzzy) & (" {}=".format(key) in p):
                        key_line = p
                    elif fuzzy & (key in p):
                        key_line = p
                key_lines.append(key_line.replace("\n", ""))
        return key_lines

    def write_profile(self, updated_lines):
        if self.other_profile_flag:
            prof_name = [self.other_profile_filename, self.profile_filename]
        else:
            prof_name = [self.profile_filename]

        for p in prof_name:
            with open(p, 'w') as writer:
                writer.writelines(updated_lines)

    def update_profile(self, key, value):
        for l in self.profile_lines:
            if key in l:
                self.profile_lines.remove(l)

        if isinstance(value, str):
            new_line = 'export {}="{}"\n'.format(key, value)
            self.profile_lines.append(new_line)
        self.write_profile(self.profile_lines)


class Encryption:
    def __init__(self, secret_key):
        self.secret_key = secret_key[0:32]
        self.cipher = AES.new(self.secret_key, AES.MODE_ECB)

    def decode(self, encoded):
        return self.cipher.decrypt(base64.b64decode(encoded)).decode('UTF-8').replace(" ", "")

    def encode(self, input_str):
        return base64.b64encode(self.cipher.encrypt(input_str.rjust(32)))


def bump_version():
    """
    Only run in the project root directory, this is for travis to bump the version file only!

    :return:
    """
    __root__ = os.path.abspath("")
    with open(os.path.join(__root__, 'VERSION')) as version_file:
        version = version_file.read().strip()

    all_version = version.replace('"', "").split(".")
    new_all_version = version.split(".")[:-1]
    new_all_version.append(str(int(all_version[-1]) + 1))
    new_line = '.'.join(new_all_version) + "\n"
    with open("{}/VERSION".format(__root__), "w") as fp:
        fp.write(new_line)
    fp.close()
