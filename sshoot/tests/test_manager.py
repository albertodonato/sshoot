import os
import yaml
from unittest import TestCase
from tempfile import gettempdir
from getpass import getuser

from fixtures import TestWithFixtures, TempDir

from ..profile import Profile
from ..manager import (
    DEFAULT_CONFIG_PATH, get_rundir, Manager, ManagerProfileError)


class ManagerTests(TestWithFixtures):

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
        self.manager = Manager(
            config_path=self.config_path, rundir=self.rundir)
        self.manager.sessions_path = self.sessions_path

    def make_fake_executable(self, exit_code=0):
        """Create a fake executable logging command line parameters."""
        temp_dir = self.useFixture(TempDir()).path
        executable = os.path.join(temp_dir, 'executable')
        script = (
            '#!/bin/sh\n'
            'echo $@ > {}/cmdline\n'
            'echo -n stderr message >&2\n'
            'exit {}\n').format(temp_dir, exit_code)
        with open(executable, 'w') as fh:
            fh.write(script)
        os.chmod(executable, 0o755)
        return executable

    def test_default_paths(self):
        """A default config path is set if not specified."""
        manager = Manager()
        self.assertEqual(manager.config_path, DEFAULT_CONFIG_PATH)

    def test_paths(self):
        """The config and sessions are set in the Manager."""
        self.assertEqual(self.manager.config_path, self.config_path)
        self.assertEqual(self.manager.sessions_path, self.sessions_path)

    def test_load_config_create_dirs(self):
        """Manager.load_config creates config directories."""
        os.rmdir(self.config_path)
        os.rmdir(self.sessions_path)
        self.manager.load_config()
        self.assertTrue(os.path.isdir(self.config_path))
        self.assertTrue(os.path.isdir(self.sessions_path))

    def test_load_profiles(self):
        """Manager.load_config loads the profiles."""
        profiles = {'profile': {'subnets': ['10.0.0.0/16']}}
        with open(self.profiles_file_path, 'w') as fh:
            yaml.dump(profiles, stream=fh)
        self.manager.load_config()
        self.assertCountEqual(self.manager.get_profiles().keys(), ['profile'])

    def test_create_profile(self):
        """Manager.create_profile adds a profile with specified details."""
        self.manager.create_profile('profile', {'subnets': ['10.0.0.0/24']})
        with open(self.profiles_file_path) as fh:
            profiles = yaml.load(fh)
        self.assertEqual(profiles, {'profile': {'subnets': ['10.0.0.0/24']}})

    def test_create_profile_in_use(self):
        """Manager.create_profile raises an error if profile name is in use."""
        self.manager.create_profile('profile', {'subnets': ['10.0.0.0/24']})
        self.assertRaises(
            ManagerProfileError, self.manager.create_profile,
            'profile', {'subnets': ['10.0.0.0/16']})

    def test_create_profile_invalid_details(self):
        """Manager.create_profile raises an error on invalid profile info."""
        self.assertRaises(
            ManagerProfileError, self.manager.create_profile,
            'profile', {'wrong': 'data'})

    def test_remove_profile(self):
        """Manager.remove_profile removes the specified profile."""
        self.manager.create_profile('profile', {'subnets': ['10.0.0.0/24']})
        self.manager.remove_profile('profile')
        with open(self.profiles_file_path) as fh:
            config = yaml.load(fh)
        self.assertEqual(config, {})

    def test_remove_profile_unknown(self):
        """Manager.remove_profile raises an error if name is unknown."""
        self.assertRaises(
            ManagerProfileError, self.manager.remove_profile, 'unknown')

    def test_get_profiles(self):
        """Manager.get_profiles returns defined profiles."""
        self.manager.create_profile('profile1', {'subnets': ['10.0.0.0/24']})
        self.manager.create_profile(
            'profile2', {'subnets': ['192.168.0.0/16']})
        profiles = {
            'profile1': Profile.from_dict({'subnets': ['10.0.0.0/24']}),
            'profile2': Profile.from_dict({'subnets': ['192.168.0.0/16']})}
        self.assertEqual(self.manager.get_profiles(), profiles)

    def test_get_profile(self):
        """Manager.get_profile returns a profile."""
        config = {'subnets': ['10.0.0.0/24']}
        self.manager.create_profile('profile', config)
        profile = self.manager.get_profile('profile')
        self.assertEqual(profile, Profile.from_dict(config))

    def test_get_profile_unknown(self):
        """Manager.get_profile raises an error if the name is unknown."""
        self.assertRaises(
            ManagerProfileError, self.manager.get_profile, 'unknown')

    def test_start_profile(self):
        """Manager.start_profile starts a profile."""
        self.manager.create_profile('profile', {'subnets': ['10.0.0.0/24']})
        executable = self.make_fake_executable()
        self.manager._get_executable = lambda: executable

        self.manager.start_profile('profile')
        output_file = os.path.join(os.path.dirname(executable), 'cmdline')
        with open(output_file) as fh:
            cmdline = fh.read()
        expected_cmdline = (
            '10.0.0.0/24 --daemon --pidfile {}/profile.pid\n'.format(
                self.sessions_path))
        self.assertEqual(cmdline, expected_cmdline)

    def test_start_profile_extra_args(self):
        """Manager.start_profile can add extra arguments to command line."""
        self.manager.create_profile('profile', {'subnets': ['10.0.0.0/24']})
        executable = self.make_fake_executable()
        self.manager._get_executable = lambda: executable

        self.manager.start_profile(
            'profile', extra_args=['--extra1', '--extra2'])
        output_file = os.path.join(os.path.dirname(executable), 'cmdline')
        with open(output_file) as fh:
            cmdline = fh.read()
        expected_cmdline = (
            '10.0.0.0/24 --daemon --pidfile {}/profile.pid --extra1 --extra2\n'
            .format(self.sessions_path))
        self.assertEqual(cmdline, expected_cmdline)

    def test_start_profile_fail(self):
        """An error is raised if starting a profile fails."""
        self.manager.create_profile('profile', {'subnets': ['10.0.0.0/24']})
        executable = self.make_fake_executable(exit_code=1)
        self.manager._get_executable = lambda: executable
        with self.assertRaises(ManagerProfileError) as context:
            self.manager.start_profile('profile')
        self.assertEqual(
            str(context.exception),
            'Profile failed to start: stderr message')

    def test_start_profile_executable_not_found(self):
        """Profile start raises an error if executable is not found."""
        self.manager.create_profile('profile', {'subnets': ['10.0.0.0/24']})
        self.manager._get_executable = lambda: '/not/here'
        self.assertRaises(
            ManagerProfileError, self.manager.start_profile, 'profile')

    def test_start_profile_unknown(self):
        """Trying to start an unknown profile raises an error."""
        self.assertRaises(
            ManagerProfileError, self.manager.start_profile, 'unknown')

    def test_start_profile_running(self):
        """Trying to start a running profile raises an error."""
        self.manager.create_profile('profile', {'subnets': ['10.0.0.0/24']})
        # Fake profile as running
        self.manager.is_running = lambda name: True
        self.assertRaises(
            ManagerProfileError, self.manager.start_profile, 'profile')

    def test_stop_profile(self):
        """Manager.stop_profile stops a running profile."""
        self.manager.create_profile('profile', {'subnets': ['10.0.0.0/24']})
        with open(self.pid_path, 'w') as fh:
            fh.write('100\n')
        # Mock manager calls
        self.manager.is_running = lambda name: True
        calls = []
        self.manager.kill = (
            lambda pid, signal: calls.append((pid, signal)))
        self.manager.stop_profile('profile')
        self.assertEqual(calls, [(100, 15)])

    def test_stop_profile_unknown(self):
        """Trying to stop an unknown profile raises an error."""
        self.assertRaises(
            ManagerProfileError, self.manager.stop_profile, 'unknown')

    def test_stop_profile_invalid_pidfile(self):
        """If pidfile contains invalid data, stopping raises an error."""
        self.manager.create_profile('profile', {'subnets': ['10.0.0.0/24']})
        with open(self.pid_path, 'w') as fh:
            fh.write('garbage')
        self.assertRaises(
            ManagerProfileError, self.manager.stop_profile, 'profile')

    def test_stop_profile_process_not_found(self):
        """If the process fails to stop an error is raised."""
        with open(self.pid_path, 'w') as fh:
            fh.write('100\n')

        self.manager.create_profile('profile', {'subnets': ['10.0.0.0/24']})

        def kill(pid, signal):
            raise IOError()

        # Mock manager calls
        self.manager.kill = kill
        self.manager.is_running = lambda name: True
        with self.assertRaises(ManagerProfileError) as cm:
            self.manager.stop_profile('profile')
        self.assertIn('Failed to stop profile', str(cm.exception))

    def test_get_pidfile(self):
        """Manager._get_pidfile returns the pidfile path for a session."""
        self.assertEqual(self.manager._get_pidfile('profile'), self.pid_path)

    def test_is_running(self):
        """If the process is present, the profile is running."""
        with open(self.pid_path, 'w') as fh:
            fh.write('{}\n'.format(os.getpid()))
        self.assertTrue(self.manager.is_running('profile'))

    def test_is_running_no_pidfile(self):
        """If the pidfile is not found, the profile is not running."""
        self.assertFalse(self.manager.is_running('not-here'))

    def test_is_running_pidfile_empty(self):
        """If the pidfile is empty, the profile is not running."""
        fh = open(os.path.join(self.sessions_path, 'profile.pid'), 'w')
        fh.close()
        self.assertFalse(self.manager.is_running('profile'))

    def test_is_running_pidfile_no_integer(self):
        """If the pid is not an integer, the profile is not running."""
        with open(self.pid_path, 'w') as fh:
            fh.write('foo\n')
        self.assertFalse(self.manager.is_running('profile'))

    def test_is_running_pidfile_no_process(self):
        """If no process is present, the profile is not running."""
        with open(self.pid_path, 'w') as fh:
            fh.write('-100\n')
        self.assertFalse(self.manager.is_running('profile'))
        # The stale pidfile is deleted.
        self.assertFalse(os.path.exists(self.pid_path))

    def test_get_cmdline(self):
        """Manager.get_cmdline returns the command line for the profile."""
        self.manager.create_profile('profile', {'subnets': ['10.0.0.0/24']})
        pidfile = os.path.join(self.sessions_path, 'profile.pid')
        self.assertEqual(
            self.manager.get_cmdline('profile'),
            ['sshuttle', '10.0.0.0/24', '--daemon', '--pidfile', pidfile])

    def test_get_cmdline_extra_args(self):
        """Manager.get_cmdline adds passed extra arguments to command line."""
        self.manager.create_profile('profile', {'subnets': ['10.0.0.0/24']})
        pidfile = os.path.join(self.sessions_path, 'profile.pid')
        expected_cmdline = [
            'sshuttle', '10.0.0.0/24', '--daemon', '--pidfile', pidfile,
            '--extra1', '--extra2']
        self.assertEqual(
            self.manager.get_cmdline(
                'profile', extra_args=['--extra1', '--extra2']),
            expected_cmdline)

    def test_get_cmdline_executable(self):
        """Manager.get_cmdline uses the configured executable."""
        self.manager.create_profile('profile', {'subnets': ['10.0.0.0/24']})
        self.manager._get_executable = lambda: '/foo/sshuttle'

        pidfile = os.path.join(self.sessions_path, 'profile.pid')
        self.assertEqual(
            self.manager.get_cmdline('profile'),
            ['/foo/sshuttle', '10.0.0.0/24', '--daemon', '--pidfile', pidfile])


class GetRundirTests(TestCase):

    def test_rundir_path(self):
        """get_rundir returns a user-specific tempdir path."""
        rundir_path = os.path.join(gettempdir(), 'foo-{}'.format(getuser()))
        self.assertEqual(get_rundir('foo'), rundir_path)
