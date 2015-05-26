#
# This file is part of sshoot.
#
# sshoot is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# sshoot is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with sshoot.  If not, see <http://www.gnu.org/licenses/>.

import os
from io import StringIO
import yaml
from textwrap import dedent

from unittest import TestCase

from fixtures import TempDir, TestWithFixtures

from sshoot.profile import Profile
from sshoot.config import yaml_dump, Config


class YamlDumpTests(TestCase):

    def setUp(self):
        super(YamlDumpTests, self).setUp()
        self.data = {'foo': 'bar', 'baz': [1, 2]}

    def test_dump_to_string(self):
        '''The method returns YAML data as a string by default.'''
        result = yaml_dump(self.data)
        self.assertEqual(yaml.load(stream=StringIO(result)), self.data)

    def test_dump_to_file(self):
        '''The method dumps YAML data to the specified file.'''
        fh = StringIO()
        result = yaml_dump(self.data, fh=fh)
        fh.seek(0)
        self.assertIsNone(result)
        self.assertEqual(yaml.load(stream=fh), self.data)


class ConfigTests(TestWithFixtures):

    def setUp(self):
        super(ConfigTests, self).setUp()
        self.tempdir = self.useFixture(TempDir()).path
        self.config_path = os.path.join(self.tempdir, 'config.yaml')
        self.profiles_path = os.path.join(self.tempdir, 'profiles.yaml')
        self.config = Config(self.tempdir)

    def test_add_profile(self):
        '''Profiles can be added to the config.'''
        profiles = {
            'profile1': Profile(['10.0.0.0/24']),
            'profile2': Profile(['192.168.0.0/16'])}
        for name, profile in profiles.items():
            self.config.add_profile(name, profile)
        self.assertEqual(self.config.profiles, profiles)

    def test_add_profile_name_present(self):
        '''An exception is raised if the profile name is already used.'''
        self.config.add_profile('profile', Profile(['10.0.0.0/24']))
        self.assertRaises(
            KeyError, self.config.add_profile, 'profile',
            Profile(['192.168.0.0/16']))

    def test_remove_profile(self):
        '''Profiles can be removed to the config.'''
        profiles = {
            'profile1': Profile(['10.0.0.0/24']),
            'profile2': Profile(['192.168.0.0/16'])}
        for name, profile in profiles.items():
            self.config.add_profile(name, profile)
        self.config.remove_profile('profile1')
        self.assertCountEqual(self.config.profiles.keys(), ['profile2'])

    def test_remove_profile_not_present(self):
        '''An exception is raised if the profile name is not known.'''
        self.assertRaises(KeyError, self.config.remove_profile, 'profile')

    def test_load_from_file(self):
        '''The config is loaded from file.'''
        profiles = {
            'profile': {
                'subnets': ['10.0.0.0/24'],
                'auto-nets': True}}
        with open(self.profiles_path, 'w') as fh:
            yaml.dump(profiles, stream=fh)
        self.config.load()
        profile = self.config.profiles['profile']
        self.assertEqual(profile.subnets, ['10.0.0.0/24'])
        self.assertTrue(profile.auto_nets)

    def test_load_missing(self):
        '''If no config files are found, config is empty.'''
        self.config.load()
        self.assertEqual(self.config.profiles, {})
        self.assertEqual(self.config.config, {})

    def test_load_config_options(self):
        '''Only known config options are loaded from config file.'''
        config = {'executable': '/usr/bin/shuttle', 'other-conf': 'no'}
        with open(self.config_path, 'w') as fh:
            yaml.dump(config, stream=fh)
        self.config.load()
        self.assertEqual(
            self.config.config, {'executable': '/usr/bin/shuttle'})

    def test_load_profiles(self):
        '''The 'profiles' config field is loaded from the config file.'''
        profiles = {
            'profile1': {'subnets': ['10.0.0.0/24']},
            'profile2': {'subnets': ['192.168.0.0/16']}}
        with open(self.profiles_path, 'w') as fh:
            yaml.dump(profiles, stream=fh)
        self.config.load()
        expected = {
            name: Profile.from_dict(config)
            for name, config in profiles.items()}
        self.assertEqual(self.config.profiles, expected)

    def test_save_profiles(self):
        '''Profiles are saved to file.'''
        profiles = {
            'profile1': {'subnets': ['10.0.0.0/24'], 'remote': 'hostname1'},
            'profile2': {'subnets': ['192.168.0.0/16'], 'remote': 'hostname2'}}
        self.config.load()
        for name, conf in profiles.items():
            self.config.add_profile(name, Profile.from_dict(conf))
        self.config.save()
        with open(self.profiles_path) as fh:
            config = yaml.load(fh)
        self.assertEqual(config, profiles)

    def test_save_from_file(self):
        '''The config is saved to file.'''
        conf = {'subnets': ['10.0.0.0/24'], 'auto_nets': True}
        self.config.add_profile('profile', Profile.from_dict(conf))
        self.config.save()

        config = dedent(
            '''\
            profile:
              auto-nets: true
              subnets:
              - 10.0.0.0/24
            ''')
        with open(self.profiles_path) as fh:
            content = fh.read()
        self.assertEqual(content, config)
