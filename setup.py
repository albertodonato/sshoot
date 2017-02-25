from setuptools import setup, find_packages

from sshoot import __version__, __doc__ as description


config = {
    'name': 'sshoot',
    'version': __version__,
    'license': 'GPLv3+',
    'description': description,
    'long_description': open('README.rst').read(),
    'author': 'Alberto Donato',
    'author_email': 'alberto.donato@gmail.com',
    'maintainer': 'Alberto Donato',
    'maintainer_email': 'alberto.donato@gmail.com',
    'url': 'https://bitbucket.org/ack/sshoot',
    'download_url': 'https://bitbucket.org/ack/sshoot/downloads',
    'packages': find_packages(),
    'include_package_data': True,
    'entry_points': {'console_scripts': ['sshoot = sshoot.main:sshoot']},
    'test_suite': 'sshoot',
    'install_requires': ['PyYAML', 'prettytable', 'argcomplete'],
    'tests_require': ['fixtures'],
    'keywords': 'ssh sshuttle vpn',
    'classifiers': [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        ('License :: OSI Approved :: '
         'GNU General Public License v3 or later (GPLv3+)'),
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: System :: Networking',
        'Topic :: Utilities']}

setup(**config)
