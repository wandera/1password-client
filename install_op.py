import os
import wget
import zipfile
import platform
from subprocess import Popen, PIPE


platform_links = {
    "Darwin": {
        "x86_64": "https://cache.agilebits.com/dist/1P/op/pkg/v1.8.0/op_darwin_amd64_v1.8.0.pkg",
        "download_loc": "/usr/local/bin/"
    },
    "FreeBSD": {
        "i386": "https://cache.agilebits.com/dist/1P/op/pkg/v1.8.0/op_freebsd_386_v1.8.0.zip",
        "i686": "https://cache.agilebits.com/dist/1P/op/pkg/v1.8.0/op_freebsd_386_v1.8.0.zip",
        "x86_64": "https://cache.agilebits.com/dist/1P/op/pkg/v1.8.0/op_freebsd_amd64_v1.8.0.zip",
        "arm": "https://cache.agilebits.com/dist/1P/op/pkg/v1.8.0/op_freebsd_arm_v1.8.0.zip",
        "aarch64_be": "https://cache.agilebits.com/dist/1P/op/pkg/v1.8.0/op_freebsd_arm_v1.8.0.zip",
        "aarch64": "https://cache.agilebits.com/dist/1P/op/pkg/v1.8.0/op_freebsd_arm_v1.8.0.zip",
        "armv8b": "https://cache.agilebits.com/dist/1P/op/pkg/v1.8.0/op_freebsd_arm_v1.8.0.zip",
        "armv8l": "https://cache.agilebits.com/dist/1P/op/pkg/v1.8.0/op_freebsd_arm_v1.8.0.zip",
        "download_loc": "/usr/local/bin/"
    },
    "Linux": {
        "i386": "https://cache.agilebits.com/dist/1P/op/pkg/v1.8.0/op_linux_386_v1.8.0.zip",
        "i686": "https://cache.agilebits.com/dist/1P/op/pkg/v1.8.0/op_linux_386_v1.8.0.zip",
        "x86_64": "https://cache.agilebits.com/dist/1P/op/pkg/v1.8.0/op_linux_amd64_v1.8.0.zip",
        "aarch64_be": "https://cache.agilebits.com/dist/1P/op/pkg/v1.8.0/op_linux_arm_v1.8.0.zip",
        "aarch64": "https://cache.agilebits.com/dist/1P/op/pkg/v1.8.0/op_linux_arm_v1.8.0.zip",
        "armv8b": "https://cache.agilebits.com/dist/1P/op/pkg/v1.8.0/op_linux_arm_v1.8.0.zip",
        "armv8l": "https://cache.agilebits.com/dist/1P/op/pkg/v1.8.0/op_linux_arm_v1.8.0.zip",
        "arm": "https://cache.agilebits.com/dist/1P/op/pkg/v1.8.0/op_linux_arm_v1.8.0.zip",
        "download_loc": "/usr/local/bin/"
    },
    "OpenBSD": {
        "i386": "https://cache.agilebits.com/dist/1P/op/pkg/v1.8.0/op_openbsd_386_v1.8.0.zip",
        "i686": "https://cache.agilebits.com/dist/1P/op/pkg/v1.8.0/op_openbsd_386_v1.8.0.zip",
        "x86_64": "https://cache.agilebits.com/dist/1P/op/pkg/v1.8.0/op_openbsd_amd64_v1.8.0.zip",
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


def check_install_required():  # pragma: no cover
    """
    Helper function to check if op cli is already installed

    :returns: :obj:`bool`: True or False

     """
    op = read_bash_return("op --version")
    if op == "":
        return True
    else:
        return False


def install_op():  # pragma: no cover
    """
    Helper function to download, unzip, install and chmod op cli files
    """
    system = str(platform.system())
    machine = str(platform.machine())
    link = platform_links[system][machine]
    local_bin = platform_links[system]["download_loc"]
    os.chmod(local_bin, 0o755)
    op_file = link.split("/")[-1]
    download_path = os.path.join(local_bin, op_file)
    print('Downloading the 1Password CLI: {}'.format(op_file))
    wget.download(link, download_path)
    if link[-4:] != ".pkg":
        zip_ref = zipfile.ZipFile(download_path, 'r')
        zip_ref.extractall(local_bin)
        zip_ref.close()
        os.chmod(os.path.join(local_bin, 'op'), 0o755)
    else:
        if check_install_required():
            Popen(["open", os.path.join(local_bin, op_file)], stdin=PIPE, stdout=PIPE)  # pragma: no cover
        else:
            pass


def install_chocolatey():
    """
    Helper function for installing Windows package management requires that installation performed in admin role
    """
    pass
