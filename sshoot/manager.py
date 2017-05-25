"""Handle sshuttle sessions."""

import os
from signal import SIGTERM
from tempfile import gettempdir
from getpass import getuser
from subprocess import Popen, PIPE

from .profile import Profile, ProfileError
from .config import Config


DEFAULT_CONFIG_PATH = os.path.expanduser(os.path.join('~', '.sshoot'))


def get_rundir(prefix):
    """Return the directory holding runtime data."""
    return os.path.join(
        gettempdir(), '{prefix}-{username}'.format(
            prefix=prefix, username=getuser()))


class ManagerProfileError(Exception):
    """Profile management failed."""


class Manager(object):

    kill = os.kill  # for testing

    def __init__(self, config_path=None, rundir=None):
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.rundir = rundir or get_rundir('sshoot')
        self.sessions_path = os.path.join(self.rundir, 'sessions')
        self._config = Config(self.config_path)

    def load_config(self):
        """Load configuration from file."""
        if not os.path.exists(self.config_path):
            os.makedirs(self.config_path)
        if not os.path.exists(self.sessions_path):
            os.makedirs(self.sessions_path)

        self._config.load()

    def create_profile(self, name, details):
        """Create a profile with provided details."""
        try:
            profile = Profile.from_dict(details)
            self._config.add_profile(name, profile)
        except KeyError:
            raise ManagerProfileError(
                'Profile name already in use: {}'.format(name))
        except ProfileError as error:
            raise ManagerProfileError(str(error))

        self._config.save()

    def remove_profile(self, name):
        """Remove profile with given name."""
        try:
            self._config.remove_profile(name)
        except KeyError:
            raise ManagerProfileError('Unknown profile: {}'.format(name))

        self._config.save()

    def get_profiles(self):
        """Return profiles defined in config."""
        return self._config.profiles

    def get_profile(self, name):
        """Return profile with given name."""
        try:
            return self._config.profiles[name]
        except KeyError:
            raise ManagerProfileError('Unknown profile: {}'.format(name))

    def start_profile(self, name, extra_args=None):
        """Start profile with given name."""
        if self.is_running(name):
            raise ManagerProfileError('Profile is already running')

        cmdline = self.get_cmdline(name, extra_args=extra_args)
        message = 'Profile failed to start: {}'
        try:
            process = Popen(cmdline, stderr=PIPE)
            # Wait until process is started (it daemonizes)
            process.wait()
        except OSError as error:
            # To catch file not found errors
            raise ManagerProfileError(message.format(error))

        if process.returncode != 0:
            error = process.stderr.read().decode()
            process.stderr.close()
            raise ManagerProfileError(message.format(error))
        process.stderr.close()

    def stop_profile(self, name):
        """Stop profile with given name."""
        self.get_profile(name)

        if not self.is_running(name):
            raise ManagerProfileError('Profile is not running')

        try:
            with open(self._get_pidfile(name)) as fh:
                self.kill(int(fh.read()), SIGTERM)
        except (IOError, OSError) as error:
            raise ManagerProfileError(
                'Failed to stop profile: {}'.format(error))

    def is_running(self, name):
        """Return whether the specified profile is running."""
        pidfile = self._get_pidfile(name)
        try:
            with open(pidfile) as fh:
                pid = int(fh.read())
        except Exception:
            # If anything fails, a valid PID can't be found, so the profile is
            # not running
            return False

        try:
            self.kill(pid, 0)
        except OSError:
            # Delete stale pidfile
            os.unlink(pidfile)
            return False
        return True

    def get_cmdline(self, name, extra_args=None):
        """Return the command line for the specified profile."""
        profile = self.get_profile(name)

        executable = self._get_executable()
        extra_opts = ['--daemon', '--pidfile', self._get_pidfile(name)]
        if extra_args:
            extra_opts.extend(extra_args)
        return profile.cmdline(executable=executable, extra_opts=extra_opts)

    def _get_pidfile(self, name):
        """Return the path of the pidfile for the specified profile."""
        return os.path.join(self.sessions_path, '{}.pid'.format(name))

    def _get_executable(self):
        """Return the shuttle executable from the config."""
        return self._config.config.get('executable', 'sshuttle')
