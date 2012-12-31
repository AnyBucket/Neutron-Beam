import sys

from setuptools import setup, find_packages

setup(
    name = "neutron-beam",
    version = '12.12.3',
    description = "Client to beam files to and from Neutron Drive.",
    url = "https://github.com/pizzapanther/Neutron-Beam",
    author = "Paul Bailey",
    author_email = "paul.m.bailey@gmail.com",
    license = "BSD",
    packages = ['nbeam', 'nbeam.SimpleAES'],
    install_requires = [
      'tornado>=2.4',
      'python-daemon>=1.5',
      'chardet>=2.1'
    ],
    entry_points = {
        "console_scripts": [
            "nbeam = nbeam.run:commander",
        ],
    },
)
