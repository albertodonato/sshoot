#
# This file is part of sshoot.

# sshoot is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.

# sshoot is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with sshoot.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import setup, find_packages

from sshoot.version import __version__


config = {
    "name": "sshoot",
    "version": __version__,
    "license": "GPLv3",
    "description": "Manage multiple sshuttle VPN sessions.",
    "long_description": open("README.rst").read(),
    "author": "Alberto Donato",
    "author_email": "<alberto.donato@gmail.com>",
    "maintainer": "Alberto Donato",
    "maintainer_email": "<alberto.donato@gmail.com>",
    "url": "https://launchpad.net/sshoot",
    "download_url": "https://launchpad.net/sshoot/+download",
    "packages": find_packages(exclude=["*.test.*", "*.test", "test.*"]),
    "include_package_data": True,
    "entry_points": {
        "console_scripts": [
            "sshoot = sshoot.scripts.main:sshoot"]},
    "install_requires": ["prettytable"],
    "tests_require": ["fixtures"],
    "keywords": "ssh sshuttle vpn",
    "classifiers": [
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        ("License :: OSI Approved :: "
         "GNU General Public License v3 or later (GPLv3+)"),
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: System :: Networking",
        "Topic :: Utilities"]}

setup(**config)
