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

"""Handle configuration files."""

import yaml
import os

from sshoot.profile import Profile


def yaml_dump(data, fh=None):
    """Dump data in YAML format with sane defaults for readability."""
    return yaml.safe_dump(
        data, fh, default_flow_style=False, allow_unicode=True)


class Config(object):
    """Hold configuration."""

    def __init__(self, config_file):
        self._config_file = config_file
        self._profiles = {}
        self._executable = None

    def load(self):
        """Load configuration from file."""
        if not os.path.exists(self._config_file):
            return

        with open(self._config_file) as fh:
            config = yaml.load(fh)
        # Load profiles
        profiles = config.get("profiles", {})
        for name, conf in profiles.iteritems():
            self._profiles[name] = Profile.from_dict(conf)
        self._executable = config.get("executable")

    def save(self):
        """Save configuration to file."""
        with open(self._config_file, "w") as fh:
            yaml_dump(self._build_config(), fh)

    def add_profile(self, name, profile):
        """Add a profile to the configuration."""
        self._profiles[name] = profile

    def remove_profile(self, name):
        """Add the given profile to the configuration."""
        del self._profiles[name]

    @property
    def profiles(self):
        """Return a dict with profiles, using names as key."""
        return self._profiles.copy()

    @property
    def executable(self):
        """Return the sshuttle executable to use, or None if set to default."""
        return self._executable

    def _build_config(self):
        config = {}
        profiles = {
            name: profile.config() for name, profile
            in self._profiles.iteritems()}
        config["profiles"] = profiles
        if self._executable:
            config["executable"] = self._executable
        return config
