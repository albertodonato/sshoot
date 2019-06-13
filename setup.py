from pathlib import Path

from setuptools import (
    find_packages,
    setup,
)

tests_require = ['fixtures', 'pytest', 'pytest-mock']

config = {
    'name': 'sshoot',
    'version': '1.4.2',
    'license': 'GPLv3+',
    'description': 'Manage multiple sshuttle VPN sessions',
    'long_description': Path('README.rst').read_text(),
    'author': 'Alberto Donato',
    'author_email': 'alberto.donato@gmail.com',
    'maintainer': 'Alberto Donato',
    'maintainer_email': 'alberto.donato@gmail.com',
    'url': 'https://github.com/albertodonato/sshoot',
    'download_url': 'https://github.com/albertodonato/sshoot/releases',
    'packages': find_packages(include=['sshoot', 'sshoot.*']),
    'include_package_data': True,
    'entry_points': {
        'console_scripts': ['sshoot = sshoot.main:sshoot']
    },
    'test_suite': 'sshoot',
    'setup_requires': ['Babel'],
    'install_requires': ['PyYAML', 'prettytable', 'argcomplete', 'pyxdg'],
    'tests_require': tests_require,
    'extras_require': {
        'testing': tests_require
    },
    'keywords': 'ssh sshuttle vpn',
    'classifiers': [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console', 'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        (
            'License :: OSI Approved :: '
            'GNU General Public License v3 or later (GPLv3+)'),
        'Operating System :: OS Independent', 'Programming Language :: Python',
        'Topic :: System :: Networking', 'Topic :: Utilities'
    ]
}

setup(**config)
