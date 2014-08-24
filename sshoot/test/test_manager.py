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

import os
import yaml

from fixtures import TestWithFixtures, TempDir

from sshoot.manager import Manager, DEFAULT_CONFIG_PATH, ManagerProfileError


class ManagerTests(TestWithFixtures):

    def setUp(self):
        super(ManagerTests, self).setUp()
        self.config_path = self.useFixture(TempDir()).path
        self.sessions_path = os.path.join(self.config_path, "sessions")
        self.pid_path = os.path.join(self.sessions_path, "profile.pid")
        self.config_file_path = os.path.join(self.config_path, "config.yaml")
        os.mkdir(self.sessions_path)
        self.manager = Manager(config_path=self.config_path)

    def make_fake_executable(self, exit_code=0):
        """Create a fake executable logging command line parameters."""
        temp_dir = self.useFixture(TempDir()).path
        executable = os.path.join(temp_dir, "executable")
        script = (
            "#!/bin/sh\n"
            "echo $@ > {}/cmdline\n"
            "exit {}\n").format(temp_dir, exit_code)
        with open(executable, "w") as fh:
            fh.write(script)
        os.chmod(executable, 0755)
        return executable

    def test_default_paths(self):
        """A default config path is set if not specified."""
        manager = Manager()
        self.assertEqual(manager.config_path, DEFAULT_CONFIG_PATH)
        sessions_path = os.path.join(DEFAULT_CONFIG_PATH, "sessions")
        self.assertEqual(manager.sessions_path, sessions_path)

    def test_paths(self):
        """The config and sessions are set in the Manager."""
        self.assertEqual(self.manager.config_path, self.config_path)
        self.assertEqual(self.manager.sessions_path, self.sessions_path)

    def test_load_config_create_dirs(self):
        """Manager.load_config creates config directories."""
        self.manager.load_config()
        self.assertTrue(os.path.isdir(self.config_path))
        self.assertTrue(os.path.isdir(self.sessions_path))

    def test_load_config(self):
        """Manager.load_config loads the config in the specified directory."""
        with open(self.config_file_path, "w") as fh:
            config = {
                "profiles": {"profile": {"subnets": ["10.0.0.0/16"]}}}
            yaml.dump(config, stream=fh)
        self.manager.load_config()
        self.assertEqual(self.manager.config.profiles.keys(), ["profile"])

    def test_create_profile(self):
        """Manager.create_profile adds a profile with specified details."""
        self.manager.create_profile("profile", {"subnets": ["10.0.0.0/24"]})
        with open(self.config_file_path) as fh:
            config = yaml.load(fh)
        self.assertEqual(
            config, {"profiles": {"profile": {"subnets": ["10.0.0.0/24"]}}})

    def test_create_profile_in_use(self):
        """Manager.create_profile raises an error if profile name is in use."""
        self.manager.create_profile("profile", {"subnets": ["10.0.0.0/24"]})
        self.assertRaises(
            ManagerProfileError, self.manager.create_profile,
            "profile", {"subnets": ["10.0.0.0/16"]})

    def test_create_profile_invalid_details(self):
        """Manager.create_profile raises an error on invalid profile info."""
        self.assertRaises(
            ManagerProfileError, self.manager.create_profile,
            "profile", {"wrong": "data"})

    def test_remove_profile(self):
        """Manager.remove_profile removes the specified profile."""
        self.manager.create_profile("profile", {"subnets": ["10.0.0.0/24"]})
        self.manager.remove_profile("profile")
        with open(self.config_file_path) as fh:
            config = yaml.load(fh)
        self.assertEqual(config["profiles"], {})

    def test_remove_profile_unknown(self):
        """Manager.remove_profile raises an error if name is unknown."""
        self.assertRaises(
            ManagerProfileError, self.manager.remove_profile, "unknown")

    def test_start_profile(self):
        """Manager.start_profile starts a profile."""
        self.manager.create_profile("profile", {"subnets": ["10.0.0.0/24"]})
        self.manager.config._executable = self.make_fake_executable()
        self.manager.start_profile("profile")
        # self.assertTrue(os.path.exists(self.pid_path)) XXXXX
        output_file = os.path.join(
            os.path.dirname(self.manager.config._executable), "cmdline")
        with open(output_file) as fh:
            cmdline = fh.read()
        expected_cmdline = (
            "10.0.0.0/24 --daemon --pidfile {}/profile.pid\n".format(
                self.sessions_path))
        self.assertEqual(cmdline, expected_cmdline)

    def test_start_profile_fail(self):
        """An error if starting a profile fails."""
        self.manager.create_profile("profile", {"subnets": ["10.0.0.0/24"]})
        self.manager.config._executable = self.make_fake_executable(
            exit_code=1)
        self.assertRaises(
            ManagerProfileError, self.manager.start_profile, "profile")

    def test_start_profile_executable_not_found(self):
        """Profile start raises an error if executable is not found."""
        self.manager.create_profile("profile", {"subnets": ["10.0.0.0/24"]})
        self.manager.config._executable = "/not/here"
        self.assertRaises(
            ManagerProfileError, self.manager.start_profile, "profile")

    def test_start_profile_unknown(self):
        """Trying to start an unknown profile raises an error."""
        self.assertRaises(
            ManagerProfileError, self.manager.start_profile, "unknown")

    def test_start_profile_running(self):
        """Trying to start a running profile raises an error."""
        self.manager.create_profile("profile", {"subnets": ["10.0.0.0/24"]})
        # Fake profile as running
        self.manager.is_running = lambda name: True
        self.assertRaises(
            ManagerProfileError, self.manager.start_profile, "profile")

    def test_stop_profile(self):
        """Manager.stop_profile stops a running profile."""
        self.manager.create_profile("profile", {"subnets": ["10.0.0.0/24"]})
        with open(self.pid_path, "w") as fh:
            fh.write("100\n")
        # Mock manager calls
        self.manager.is_running = lambda name: True
        calls = []
        self.manager.kill = (
            lambda pid, signal: calls.append((pid, signal)))
        self.manager.stop_profile("profile")
        self.assertEqual(calls, [(100, 15)])

    def test_stop_profile_unknown(self):
        """Trying to stop an unknown profile raises an error."""
        self.assertRaises(
            ManagerProfileError, self.manager.stop_profile, "unknown")

    def test_stop_profile_invalid_pidfile(self):
        """If pidfile contains invalid data, stopping raises an error."""
        self.manager.create_profile("profile", {"subnets": ["10.0.0.0/24"]})
        with open(self.pid_path, "w") as fh:
            fh.write("garbage\n")
        self.assertRaises(
            ManagerProfileError, self.manager.stop_profile, "profile")

    def test_wb_get_pidfile(self):
        """Manager._get_pidfile returns the pidfile path for a session."""
        self.assertEqual(self.manager._get_pidfile("profile"), self.pid_path)

    def test_is_running(self):
        """If the process is present, the profile is running."""
        with open(self.pid_path, "w") as fh:
            fh.write("{}\n".format(os.getpid()))
        self.assertTrue(self.manager.is_running("profile"))

    def test_is_running_no_pidfile(self):
        """If the pidfile is not found, the profile is not running."""
        self.assertFalse(self.manager.is_running("not-here"))

    def test_is_running_pidfile_empty(self):
        """If the pidfile is empty, the profile is not running."""
        fh = open(os.path.join(self.sessions_path, "profile.pid"), "w")
        fh.close()
        self.assertFalse(self.manager.is_running("profile"))

    def test_is_running_pidfile_no_integer(self):
        """If the pid is not an integer, the profile is not running."""
        with open(self.pid_path, "w") as fh:
            fh.write("foo\n")
        self.assertFalse(self.manager.is_running("profile"))

    def test_is_running_pidfile_no_process(self):
        """If no process is present, the profile is not running."""
        with open(self.pid_path, "w") as fh:
            fh.write("-100\n")
        self.assertFalse(self.manager.is_running("profile"))
        # The stale pidfile is deleted.
        self.assertFalse(os.path.exists(self.pid_path))
