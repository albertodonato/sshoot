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
from StringIO import StringIO
import yaml

from unittest import TestCase

from fixtures import TempDir, TestWithFixtures

from sshoot.profile import Profile
from sshoot.config import yaml_dump, Config


class YamlDumpTests(TestCase):

    def setUp(self):
        super(YamlDumpTests, self).setUp()
        self.data = {"foo": "bar", "baz": [1, 2]}

    def test_dump_to_string(self):
        """The method returns YAML data as a string by default."""
        result = yaml_dump(self.data)
        self.assertEqual(yaml.load(stream=StringIO(result)), self.data)

    def test_dump_to_file(self):
        """The method dumps YAML data to the specified file."""
        fh = StringIO()
        result = yaml_dump(self.data, fh=fh)
        fh.seek(0)
        self.assertIsNone(result)
        self.assertEqual(yaml.load(stream=fh), self.data)


class ConfigTests(TestWithFixtures):

    def setUp(self):
        super(ConfigTests, self).setUp()
        self.tempdir = self.useFixture(TempDir())
        self.config_name = os.path.join(self.tempdir.path, "config.yaml")
        self.config = Config(self.config_name)

    def test_add_profile(self):
        """Profiles can be added to the config."""
        profiles = {
            "profile1": Profile(["10.0.0.0/24", "192.168.0.0/16"]),
            "profile2": Profile(["10.0.0.0/24", "192.168.0.0/16"])}
        for name, profile in profiles.iteritems():
            self.config.add_profile(name, profile)
        self.assertEqual(self.config.profiles, profiles)

    def test_remove_profile(self):
        """Profiles can be removed to the config."""
        profiles = {
            "profile1": Profile(["10.0.0.0/24", "192.168.0.0/16"]),
            "profile2": Profile(["10.0.0.0/24", "192.168.0.0/16"])}
        for name, profile in profiles.iteritems():
            self.config.add_profile(name, profile)
        self.config.remove_profile("profile1")
        self.assertEqual(["profile2"], self.config.profiles.keys())

    def test_load_missing(self):
        """If no config file is found, config is empty."""
        self.config.load()
        self.assertEqual(self.config.profiles, {})
        self.assertIsNone(self.config.executable)

    def test_load_executable(self):
        """The "executable" config field is loaded from the config file."""
        with open(self.config_name, "w") as fh:
            yaml.dump({"executable": "/usr/local/bin/sshuttle"}, stream=fh)
        self.config.load()
        self.assertEqual(self.config.executable, "/usr/local/bin/sshuttle")

    def test_load_profiles(self):
        """The "profiles" config field is loaded from the config file."""
        profiles = {
            "profile1": {"subnets": ["10.0.0.0/24"]},
            "profile2": {"subnets": ["192.168.0.0/16"]}}
        with open(self.config_name, "w") as fh:
            yaml.dump({"profiles": profiles}, stream=fh)
        self.config.load()
        expected = {
            name: Profile.from_dict(config)
            for name, config in profiles.iteritems()}
        self.assertEqual(self.config.profiles, expected)

    def test_save_empty_config(self):
        """Empty conifguration is saved to file, without default values."""
        self.config.save()
        with open(self.config_name) as fh:
            config = yaml.load(fh)
        # The "executable" field is not saved.
        self.assertEqual(config, {"profiles": {}})

    def test_save_executable(self):
        """The "executable" attribute is saved to config file."""
        self.config._executable = "/usr/local/bin/sshuttle"
        self.config.save()
        with open(self.config_name) as fh:
            config = yaml.load(fh)
        self.assertEqual(config["executable"], "/usr/local/bin/sshuttle")

    def test_save_profiles(self):
        """Profiles are saved to config file."""
        profiles = {
            "profile1": {"subnets": ["10.0.0.0/24"], "remote": "hostname1"},
            "profile2": {"subnets": ["192.168.0.0/16"], "remote": "hostname2"}}
        self.config.load()
        for name, conf in profiles.iteritems():
            self.config.add_profile(name, Profile.from_dict(conf))
        self.config.save()
        with open(self.config_name) as fh:
            config = yaml.load(fh)
        self.assertEqual(config["profiles"], profiles)
