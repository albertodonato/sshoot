"""Handle sshuttle sessions."""

from getpass import getuser
import os
from pathlib import Path
from signal import (
    SIGKILL,
    SIGTERM,
)
from subprocess import (
    PIPE,
    Popen,
)
from tempfile import gettempdir
import time
from typing import (
    Any,
    cast,
    Dict,
    IO,
    List,
    Optional,
)

from xdg.BaseDirectory import xdg_config_home

from .config import Config
from .i18n import _
from .profile import (
    Profile,
    ProfileError,
)

DEFAULT_CONFIG_PATH = Path(xdg_config_home) / "sshoot"


class ManagerProfileError(Exception):
    """Profile operation failed."""


class Manager:
    """Profile manager."""

    def __init__(self, config_path: Optional[str] = None, rundir: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        self.rundir = Path(rundir) if rundir else get_rundir("sshoot")
        self.sessions_path = self.rundir / "sessions"
        self._config = Config(self.config_path)

    def load_config(self):
        """Load configuration from file."""
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.sessions_path.mkdir(parents=True, exist_ok=True)
        self._config.load()

    def create_profile(self, name: str, details: Dict[str, Any]):
        """Create a profile with provided details."""
        try:
            self._config.add_profile(name, Profile.from_config(details))
        except KeyError:
            raise ManagerProfileError(
                _("Profile name already in use: {name}").format(name=name)
            )
        except ProfileError as error:
            raise ManagerProfileError(str(error))
        self._config.save()

    def remove_profile(self, name: str):
        """Remove profile with given name."""
        try:
            self._config.remove_profile(name)
        except KeyError:
            raise ManagerProfileError(_("Unknown profile: {name}").format(name=name))

        self._config.save()

    def get_profiles(self) -> Dict[str, Profile]:
        """Return profiles defined in config."""
        return self._config.profiles

    def get_profile(self, name: str) -> Profile:
        """Return profile with given name."""
        try:
            return self._config.profiles[name]
        except KeyError:
            raise ManagerProfileError(_("Unknown profile: {name}").format(name=name))

    def start_profile(self, name: str, extra_args: Optional[List[str]] = None):
        """Start profile with given name."""
        if self.is_running(name):
            raise ManagerProfileError(_("Profile is already running"))

        cmdline = self.get_cmdline(name, extra_args=extra_args)
        message = _("Profile failed to start: {error}")
        try:
            process = Popen(cmdline, stderr=PIPE)
            # Wait until process is started (it daemonizes)
            process.wait()
        except OSError as err:
            # To catch file not found errors
            raise ManagerProfileError(message.format(error=str(err)))

        stderr = cast(IO[bytes], process.stderr)
        if process.returncode != 0:
            error = stderr.read().decode()
            stderr.close()
            raise ManagerProfileError(message.format(error=error))
        stderr.close()

    def stop_profile(self, name: str):
        """Stop profile with given name."""
        self.get_profile(name)

        if not self.is_running(name):
            raise ManagerProfileError(_("Profile is not running"))

        try:
            pid = int(self._get_pidfile(name).read_text())
            kill_and_wait(pid)
        except (IOError, OSError, PermissionError) as error:
            raise ManagerProfileError(
                _("Failed to stop profile: {error}").format(error=error)
            )

    def restart_profile(self, name: str, extra_args: Optional[List[str]] = None):
        """Restart profile with given name."""
        if self.is_running(name):
            self.stop_profile(name)
        self.start_profile(name, extra_args=extra_args)

    def is_running(self, name: str) -> bool:
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
        except ProcessLookupError:
            # Delete stale pidfile
            pidfile.unlink()
            return False
        return True

    def get_cmdline(
        self, name: str, extra_args: Optional[List[str]] = None
    ) -> List[str]:
        """Return the command line for the specified profile."""
        profile = self.get_profile(name)

        executable = self._get_executable()
        extra_opts = ["--daemon", "--pidfile", str(self._get_pidfile(name))]
        if extra_args:
            extra_opts.extend(extra_args)
        return profile.cmdline(executable=executable, extra_opts=extra_opts)

    def _get_pidfile(self, name: str) -> Path:
        """Return the path of the pidfile for the specified profile."""
        return self.sessions_path / "{}.pid".format(name)

    def _get_executable(self) -> str:
        """Return the shuttle executable from the config."""
        return self._config.config.get("executable", "sshuttle")


class ProcessKillFail(Exception):
    """Failed to kill a process."""

    def __init__(self, pid: int):
        self.pid = pid
        super().__init__(_("Failed to kill process {pid}").format(pid=pid))


def kill_and_wait(pid: int):
    """Kill a process and wait for it to terminate."""
    for wait, signal in ((2.0, SIGTERM), (1.0, SIGKILL)):
        while wait > 0:
            try:
                os.kill(pid, signal)
            except ProcessLookupError:
                return
            wait -= 0.2
            time.sleep(0.2)
    raise ProcessKillFail(pid)


def get_rundir(prefix: str) -> Path:
    """Return the directory holding runtime data."""
    return Path(gettempdir()) / "{prefix}-{username}".format(
        prefix=prefix, username=getuser()
    )
