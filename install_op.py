import os
import wget
import zipfile
import platform
from subprocess import Popen, PIPE


cli_version = "2.19.0"
version_string = "v{}".format(cli_version)
os.environ["OP_VERSION_STR"] = version_string
platform_links = {
    "Darwin": {
        "x86_64": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_apple_universal_{}.pkg".format(version_string,
                                                                                                   version_string),
        "arm64": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_apple_universal_{}.pkg".format(version_string,
                                                                                                   version_string),
        "download_loc": "/usr/local/bin/"
    },
    "FreeBSD": {
        "i386": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_freebsd_386_{}.zip".format(version_string,
                                                                                             version_string),
        "i686": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_freebsd_386_{}.zip".format(version_string,
                                                                                             version_string),
        "x86_64": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_freebsd_amd64_{}.zip".format(version_string,
                                                                                                 version_string),
        "arm": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_freebsd_arm_{}.zip".format(version_string,
                                                                                            version_string),
        "aarch64_be": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_freebsd_arm_{}.zip".format(version_string,
                                                                                                   version_string),
        "aarch64": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_freebsd_arm_{}.zip".format(version_string,
                                                                                                version_string),
        "armv8b": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_freebsd_arm_{}.zip".format(version_string,
                                                                                               version_string),
        "armv8l": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_freebsd_arm_{}.zip".format(version_string,
                                                                                               version_string),
        "download_loc": "/usr/local/bin/"
    },
    "Linux": {
        "i386": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_linux_386_{}.zip".format(version_string,
                                                                                           version_string),
        "i686": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_linux_386_{}.zip".format(version_string,
                                                                                           version_string),
        "x86_64": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_linux_amd64_{}.zip".format(version_string,
                                                                                               version_string),
        "aarch64_be": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_linux_arm_{}.zip".format(version_string,
                                                                                                 version_string),
        "aarch64": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_linux_arm_{}.zip".format(version_string,
                                                                                              version_string),
        "armv8b": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_linux_arm_{}.zip".format(version_string,
                                                                                             version_string),
        "armv8l": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_linux_arm_{}.zip".format(version_string,
                                                                                             version_string),
        "arm": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_linux_arm_{}.zip".format(version_string,
                                                                                          version_string),
        "download_loc": "/usr/local/bin/"
    },
    "OpenBSD": {
        "i386": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_openbsd_386_{}.zip".format(version_string,
                                                                                             version_string),
        "i686": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_openbsd_386_{}.zip".format(version_string,
                                                                                             version_string),
        "x86_64": "https://cache.agilebits.com/dist/1P/op2/pkg/{}/op_openbsd_amd64_{}.zip".format(version_string,
                                                                                                 version_string),
        "download_loc": "/usr/local/bin/"
    }
}


def read_bash_return(cmd, single=True):
    process = os.popen(cmd)
    preprocessed = process.read()
    process.close()
    if single:
        return str(preprocessed.split("\n")[0])
    else:
        return str(preprocessed)


def mkdirpy(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


class CliInstaller:  # pragma: no cover
    def __init__(self):
        self.system = str(platform.system())
        machine = str(platform.machine())
        self.link = platform_links[self.system][machine]
        self.download_location = platform_links[self.system]["download_loc"]

    def install(self):
        if self.system in platform_links.keys():
            self.install_linux_mac()
        else:
            raise OSError("Operating system not supported")

    def check_install_required(self):  # pragma: no cover
        """
        Helper function to check if op cli is already installed

        :returns: :obj:`bool`: True or False

         """
        op = read_bash_return("op --version")
        if op == "":
            return True, self.download_location
        else:
            if op >= cli_version:
                return False, ""
            else:
                existing_location = read_bash_return("which op")
                return True, existing_location

    def install_linux_mac(self):
        """
            Helper function to download, unzip, install and chmod op cli files
            """
        install_check, install_loc = self.check_install_required()
        if install_check:
            if install_loc == self.download_location:
                local_bin = self.download_location
            else:
                local_bin = install_loc
            try:
                os.chmod(local_bin, 0o755)
            except PermissionError:
                local_bin = os.path.join(os.environ["HOME"], "op-downloads")
                mkdirpy(local_bin)
                os.chmod(local_bin, 0o755)
            op_file = self.link.split("/")[-1]
            download_path = os.path.join(local_bin, op_file)
            print('Downloading the 1Password CLI: {}'.format(op_file))
            wget.download(self.link, download_path)
            if self.link[-4:] != ".pkg":
                zip_ref = zipfile.ZipFile(download_path, 'r')
                zip_ref.extractall(local_bin)
                zip_ref.close()
                os.chmod(os.path.join(local_bin, 'op'), 0o755)
            else:
                Popen(["open", os.path.join(local_bin, op_file)], stdin=PIPE, stdout=PIPE)  # pragma: no cover
        else:
            print("op already installed, with supported version.")


if __name__ == '__main__':
    # Run wizard if executed from terminal
    install_cli = CliInstaller()
    install_cli.install()
    print()
