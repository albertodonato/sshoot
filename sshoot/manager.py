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

"""Handle sshuttle sessions."""

import os

from sshoot.config import Config

DEFAULT_CONFIG_DIR = os.path.expanduser(os.path.join("~", ".sshoot"))


class Manager(object):

    def __init__(self, config_dir=None):
        self.config_dir = config_dir or DEFAULT_CONFIG_DIR
        self.sessions_dir = os.path.join(self.config_dir, "sessions")

    def load(self):
        if not os.path.exists(self.config_dir):
            os.mkdir(self.config_dir)
        if not os.path.exists(self.sessions_dir):
            os.mkdir(self.sessions_dir)

        self.config = Config(os.path.join(self.config_dir, "config.yaml"))
        self.config.load()

    def get_pidfile(self, name):
        """Return the path of the pidfile for the specified profile."""
        return os.path.join(self.sessions_dir, "{}.pid".format(name))

    def is_running(self, name):
        """Return whether the specified profile is running."""
        pidfile = self.get_pidfile(name)
        try:
            with open(pidfile) as fh:
                pid = int(fh.read())
        except Exception:
            # If anything fails, the pid can't be signalled, so the profile is
            # not running
            return False

        try:
            os.kill(pid, 0)
        except OSError:
            # Delete stale pidfile
            os.unlink(pidfile)
            return False
        return True
