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

from unittest import TestCase

from sshoot.profile import Profile, ProfileError


class ProfileTests(TestCase):

    def setUp(self):
        super(ProfileTests, self).setUp()
        self.profile = Profile(['1.1.1.0/24', '10.10.0.0/16'])

    def test_from_dict(self):
        '''A Profile can be created from a dict with its attributes.'''
        profile = Profile.from_dict(
            {'remote': '1.2.3.4',
             'subnets': ['1.1.1.0/24', '10.10.0.0/16'],
             'dns': True,
             'auto_hosts': True})
        self.assertEqual(profile.remote, '1.2.3.4')
        self.assertEqual(profile.subnets, ['1.1.1.0/24', '10.10.0.0/16'])
        self.assertTrue(profile.dns)
        self.assertTrue(profile.auto_hosts)
        # Other attributes are set to default
        self.assertFalse(profile.auto_nets)
        self.assertIsNone(profile.exclude_subnets)
        self.assertIsNone(profile.seed_hosts)
        self.assertIsNone(profile.extra_opts)

    def test_from_dict_raise_error(self):
        '''If the 'subnets' key is missing in config, an error is raised.'''
        self.assertRaises(
            ProfileError, Profile.from_dict, {'remote': '1.2.3.4'})

    def test_cmdline(self):
        '''Profile.cmdline() return the sshuttle cmdline for the config.'''
        self.assertEqual(
            self.profile.cmdline(), ['sshuttle', '1.1.1.0/24', '10.10.0.0/16'])

    def test_cmdline_with_options(self):
        '''Profile.cmdline() return the sshuttle cmdline for the config.'''
        self.profile.remote = '1.2.3.4'
        self.profile.dns = True
        self.profile.exclude_subnets = ['10.20.0.0/16', '10.30.0.0/16']
        self.assertEqual(
            self.profile.cmdline(),
            ['sshuttle', '1.1.1.0/24', '10.10.0.0/16', '--remote=1.2.3.4',
             '--dns', '--exclude=10.20.0.0/16', '--exclude=10.30.0.0/16'])

    def test_cmdline_with_profile_extra_opts(self):
        '''Profile.cmdline() return the sshuttle cmdline with extra options.'''
        self.profile.extra_opts = ['--verbose', '--daemon']
        self.assertEqual(
            self.profile.cmdline(),
            ['sshuttle', '1.1.1.0/24', '10.10.0.0/16', '--verbose',
             '--daemon'])

    def test_cmdline_with_extra_opts(self):
        '''Profile.cmdline() includes extra options.'''
        self.assertEqual(
            self.profile.cmdline(extra_opts=['--verbose', '--daemon']),
            ['sshuttle', '1.1.1.0/24', '10.10.0.0/16', '--verbose',
             '--daemon'])

    def test_cmdline_with_executable(self):
        '''Profile.cmdline() uses the specified executable.'''
        self.assertCountEqual(
            self.profile.cmdline(executable='/bin/foo'),
            ['/bin/foo', '1.1.1.0/24', '10.10.0.0/16'])

    def test_config(self):
        '''Profile.config() returns a dict with the profile config.'''
        self.profile.remote = '1.2.3.4'
        self.profile.dns = True
        self.assertEqual(
            self.profile.config(),
            {'remote': '1.2.3.4', 'dns': True,
             'subnets': ['1.1.1.0/24', '10.10.0.0/16']})

    def test_config_rebuild_profiles(self):
        '''Result of Profile.config() can be used build an equal Profile.'''
        profile = Profile.from_dict(self.profile.config())
        self.assertEqual(profile, self.profile)

    def test_eq(self):
        '''Profiles can be tested for equality.'''
        profile = Profile(['1.1.1.0/24', '10.10.0.0/16'])
        self.assertEqual(profile, self.profile)

    def test_eq_false(self):
        '''Profiles with different config don't evaluate as equal.'''
        profile = Profile(['1.1.1.0/24', '10.10.0.0/16'])
        profile.auto_hosts = True
        self.assertNotEqual(profile, self.profile)
