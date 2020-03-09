from setuptools import setup
import os


root_dir = os.getcwd()
with open(os.path.join(root_dir, 'VERSION')) as version_file:
    version = version_file.read().strip()


def readme():
    with open('README.md') as f:
        return f.read()


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
        "pyyaml>=5.1.2",
        "bs4>=0.0.1",
        "pycryptodome>=3.9.7"
    ],
    python_requires='>=3.7',
    license="MIT",
    url="https://github.com/wandera/1password-client",
    classifiers=["Programming Language :: Python :: 3",
                 "License :: OSI Approved :: MIT License",
                 "Operating System :: MacOS :: MacOS X"],
    packages=["onepassword"],
    tests_require=["nose", "mock"],
    test_suite="nose.collector",
)
