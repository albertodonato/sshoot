"""Handle sshuttle sessions."""

from getpass import getuser
import os
from pathlib import Path
from signal import SIGTERM
from subprocess import (
    PIPE,
    Popen,
)
from tempfile import gettempdir

from xdg.BaseDirectory import xdg_config_home

from .config import Config
from .i18n import _
from .profile import (
    Profile,
    ProfileError,
)

DEFAULT_CONFIG_PATH = Path(xdg_config_home) / 'sshoot'


class ManagerProfileError(Exception):
    """Profile operation failed."""


class Manager:
    """Profile manager."""

    def __init__(self, config_path=None, rundir=None):
        self.config_path = (
            Path(config_path) if config_path else DEFAULT_CONFIG_PATH)
        self.rundir = Path(rundir) if rundir else get_rundir('sshoot')
        self.sessions_path = self.rundir / 'sessions'
        self._config = Config(self.config_path)

    def load_config(self):
        """Load configuration from file."""
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.sessions_path.mkdir(parents=True, exist_ok=True)
        self._config.load()

    def create_profile(self, name, details):
        """Create a profile with provided details."""
        try:
            profile = Profile.from_dict(details)
            self._config.add_profile(name, profile)
        except KeyError:
            raise ManagerProfileError(
                _('Profile name already in use: {name}').format(name=name))
        except ProfileError as error:
            raise ManagerProfileError(str(error))

        self._config.save()

    def remove_profile(self, name):
        """Remove profile with given name."""
        try:
            self._config.remove_profile(name)
        except KeyError:
            raise ManagerProfileError(
                _('Unknown profile: {name}').format(name=name))

        self._config.save()

    def get_profiles(self):
        """Return profiles defined in config."""
        return self._config.profiles

    def get_profile(self, name):
        """Return profile with given name."""
        try:
            return self._config.profiles[name]
        except KeyError:
            raise ManagerProfileError(
                _('Unknown profile: {name}').format(name=name))

    def start_profile(self, name, extra_args=None):
        """Start profile with given name."""
        if self.is_running(name):
            raise ManagerProfileError(_('Profile is already running'))

        cmdline = self.get_cmdline(name, extra_args=extra_args)
        message = _('Profile failed to start: {error}')
        try:
            process = Popen(cmdline, stderr=PIPE)
            # Wait until process is started (it daemonizes)
            process.wait()
        except OSError as err:
            # To catch file not found errors
            raise ManagerProfileError(message.format(error=str(err)))

        if process.returncode != 0:
            error = process.stderr.read().decode()
            process.stderr.close()
            raise ManagerProfileError(message.format(error=error))
        process.stderr.close()

    def stop_profile(self, name):
        """Stop profile with given name."""
        self.get_profile(name)

        if not self.is_running(name):
            raise ManagerProfileError(_('Profile is not running'))

        try:
            pid = int(self._get_pidfile(name).read_text())
            os.kill(pid, SIGTERM)
        except (IOError, OSError) as error:
            raise ManagerProfileError(
                _('Failed to stop profile: {error}').format(error=error))

    def is_running(self, name):
        """Return whether the specified profile is running."""
        pidfile = self._get_pidfile(name)
        try:
            pid = int(pidfile.read_text())
        except Exception:
            # If anything fails, a valid PID can't be found, so the profile is
            # not running
            return False

        try:
            os.kill(pid, 0)
        except OSError:
            # Delete stale pidfile
            pidfile.unlink()
            return False
        return True

    def get_cmdline(self, name, extra_args=None):
        """Return the command line for the specified profile."""
        profile = self.get_profile(name)

        executable = self._get_executable()
        extra_opts = ['--daemon', '--pidfile', str(self._get_pidfile(name))]
        if extra_args:
            extra_opts.extend(extra_args)
        return profile.cmdline(executable=executable, extra_opts=extra_opts)

    def _get_pidfile(self, name):
        """Return the path of the pidfile for the specified profile."""
        return self.sessions_path / '{}.pid'.format(name)

    def _get_executable(self):
        """Return the shuttle executable from the config."""
        return self._config.config.get('executable', 'sshuttle')


def get_rundir(prefix):
    """Return the directory holding runtime data."""
    return Path(gettempdir()) / '{prefix}-{username}'.format(
        prefix=prefix, username=getuser())
