import os
import json
import yaml
import csv
from io import StringIO

from fixtures import (
    TestWithFixtures,
    TempDir)

from ..manager import Manager
from ..listing import (
    InvalidFormat,
    ProfileListing,
    profile_details)


class ProfileListingTests(TestWithFixtures):

    def setUp(self):
        super().setUp()
        self.config_path = self.useFixture(TempDir()).path
        self.rundir = self.useFixture(TempDir()).path
        self.sessions_path = os.path.join(self.rundir, 'sessions')
        self.pid_path = os.path.join(self.sessions_path, 'profile.pid')
        self.profiles_file_path = os.path.join(
            self.config_path, 'profiles.yaml')
        self.config_file_path = os.path.join(self.config_path, 'config.yaml')
        os.mkdir(self.sessions_path)

        self.active_profiles = []
        self.manager = Manager(
            config_path=self.config_path, rundir=self.rundir)
        self.manager.sessions_path = self.sessions_path
        self.manager.is_running = lambda name: name in self.active_profiles

        self.profile_listing = ProfileListing(self.manager)

    def test_supported_formats(self):
        """supported_formats returns a list with supported formats."""
        self.assertEqual(
            ProfileListing.supported_formats(),
            ['csv', 'json', 'table', 'yaml'])

    def test_get_output_unsupported_format(self):
        """get_output raises an error if an unsupported format is passed."""
        self.assertRaises(
            InvalidFormat, self.profile_listing.get_output, 'unknown')

    def test_get_output_table(self):
        """Profiles can be listed as a table."""
        self.manager.create_profile('profile1', {'subnets': ['10.0.0.0/24']})
        self.manager.create_profile(
            'profile2', {'subnets': ['192.168.0.0/16']})
        self.active_profiles.append('profile2')
        output = self.profile_listing.get_output('table')
        self.assertIn('   profile1               10.0.0.0/24', output)
        self.assertIn('*  profile2               192.168.0.0/16', output)

    def test_get_output_table_verbose(self):
        """Tabular output can be verbose."""
        self.manager.create_profile(
            'profile1', {'subnets': ['10.0.0.0/24'], 'auto_hosts': True})
        self.active_profiles.append('profile2')
        output = self.profile_listing.get_output('table', verbose=True)
        self.assertIn(
            'Name      Remote host  Subnets      Auto hosts  Auto nets'
            '  DNS forward  Exclude subnets  Seed hosts  Extra options',
            output)
        self.assertIn(
            'profile1               10.0.0.0/24  True        False      False',
            output)

    def test_get_output_csv(self):
        """Profiles can be listed as CSV."""
        self.manager.create_profile('profile1', {'subnets': ['10.0.0.0/24']})
        self.manager.create_profile(
            'profile2', {'subnets': ['192.168.0.0/16']})
        self.active_profiles.append('profile2')
        output = self.profile_listing.get_output('csv')
        reader = csv.reader(StringIO(output))
        self.assertEqual(
            sorted(reader),
            [['Name', 'Status', 'Remote host', 'Subnets', 'Auto hosts',
              'Auto nets', 'DNS forward', 'Exclude subnets', 'Seed hosts',
              'Extra options'],
             ['profile1', 'STOPPED', '', "['10.0.0.0/24']", 'False', 'False',
              'False', '', '', ''],
             ['profile2', 'ACTIVE', '', "['192.168.0.0/16']", 'False', 'False',
              'False', '', '', '']])

    def test_get_output_json(self):
        """Profiles can be listed as JSON."""
        self.manager.create_profile('profile1', {'subnets': ['10.0.0.0/24']})
        self.manager.create_profile(
            'profile2', {'subnets': ['192.168.0.0/16'], 'auto_hosts': True})
        self.active_profiles.append('profile2')
        output = self.profile_listing.get_output('json')
        data = json.loads(output)
        self.assertEqual(
            data,
            {'profile1': {'subnets': ['10.0.0.0/24']},
             'profile2': {'subnets': ['192.168.0.0/16'], 'auto_hosts': True}})

    def test_get_output_yaml(self):
        """Profiles can be listed as YAML."""
        self.manager.create_profile('profile1', {'subnets': ['10.0.0.0/24']})
        self.manager.create_profile(
            'profile2', {'subnets': ['192.168.0.0/16'], 'auto_hosts': True})
        self.active_profiles.append('profile2')
        output = self.profile_listing.get_output('yaml')
        data = yaml.load(output)
        self.assertEqual(
            data,
            {'profile1': {'subnets': ['10.0.0.0/24']},
             'profile2': {'subnets': ['192.168.0.0/16'], 'auto_hosts': True}})


class ProfileDetailsTests(TestWithFixtures):

    def setUp(self):
        super().setUp()
        self.config_path = self.useFixture(TempDir()).path
        self.rundir = self.useFixture(TempDir()).path
        self.sessions_path = os.path.join(self.rundir, 'sessions')
        self.pid_path = os.path.join(self.sessions_path, 'profile.pid')
        self.profiles_file_path = os.path.join(
            self.config_path, 'profiles.yaml')
        self.config_file_path = os.path.join(self.config_path, 'config.yaml')
        os.mkdir(self.sessions_path)

        self.active_profiles = []
        self.manager = Manager(
            config_path=self.config_path, rundir=self.rundir)
        self.manager.sessions_path = self.sessions_path
        self.manager.is_running = lambda name: name in self.active_profiles

    def test_details(self):
        """profile_details returns a string with profile details."""
        self.manager.create_profile('profile', {'subnets': ['10.0.0.0/24']})
        output = profile_details(self.manager, 'profile')
        self.assertIn('Name:             profile', output)
        self.assertIn('Subnets:          10.0.0.0/24', output)
        self.assertIn('Status:           STOPPED', output)

    def test_active(self):
        """profile_details shows if the profile is active."""
        self.manager.create_profile('profile', {'subnets': ['10.0.0.0/24']})
        self.active_profiles.append('profile')
        output = profile_details(self.manager, 'profile')
        self.assertIn('Status:           ACTIVE', output)
