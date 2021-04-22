import os
from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install


class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        develop.run(self)
        from install_op import install_op
        install_op()


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        install.run(self)
        from install_op import install_op
        install_op()


def readme():
    with open('README.md') as f:
        return f.read()


root_dir = os.getcwd()
with open(os.path.join(root_dir, 'VERSION')) as version_file:
    version = version_file.read().strip()


setup(
    name="1password",
    version=version,
    author="David Pryce",
    author_email="david.pryce@wandera.com",
    description="A Python client and wrapper around the 1Password CLI.",
    long_description=readme(),
    long_description_content_type='text/markdown',
    install_requires=[
        "wget>=3.2",
        "pyyaml>=5.4",
        "pycryptodome>=3.9.7",
        "pexpect>=4.7.0"
    ],
    python_requires='>=3.7',
    license="MIT",
    url="https://github.com/wandera/1password-client",
    classifiers=["Programming Language :: Python :: 3 :: Only",
                 "License :: OSI Approved :: MIT License",
                 "Operating System :: MacOS :: MacOS X",
                 "Operating System :: POSIX",
                 "Operating System :: Unix"],
    packages=["onepassword"],
    tests_require=["nose", "mock", "pytest"],
    test_suite="nose.collector",
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },
    setup_requires=["wget"]
)
