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

from sshoot.manager import Manager, DEFAULT_CONFIG_PATH


class ManagerTests(TestWithFixtures):

    def setUp(self):
        super(ManagerTests, self).setUp()
        self.config_path = self.useFixture(TempDir()).path
        self.sessions_path = os.path.join(self.config_path, "sessions")
        self.pid_path = os.path.join(self.sessions_path, "profile.pid")
        os.mkdir(self.sessions_path)
        self.manager = Manager(config_path=self.config_path)

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
        config_file_path = os.path.join(self.config_path, "config.yaml")
        with open(config_file_path, "w") as fh:
            config = {
                "profiles": {"profile": {"subnets": ["10.0.0.0/16"]}}}
            yaml.dump(config, stream=fh)
        self.manager.load_config()
        self.assertEqual(self.manager.config.profiles.keys(), ["profile"])

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
