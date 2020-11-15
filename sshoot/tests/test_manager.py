from getpass import getuser
import os
from pathlib import Path
import signal
from tempfile import gettempdir

import pytest
import yaml

from ..manager import (
    DEFAULT_CONFIG_PATH,
    get_rundir,
    kill_and_wait,
    Manager,
    ManagerProfileError,
    ProcessKillFail,
)
from ..profile import Profile


def fake_executable(base_path, exit_code):
    """Create a fake executable logging command line parameters."""
    executable = Path(base_path) / "executable"
    executable.write_text(
        (
            "#!/bin/sh\n"
            "echo $@ > {}/cmdline\n"
            "echo -n stderr message >&2\n"
            "exit {}\n"
        ).format(str(base_path), exit_code)
    )
    executable.chmod(0o755)
    return executable


@pytest.fixture
def bin_succeed(tmpdir):
    yield fake_executable(tmpdir, 0)


@pytest.fixture
def bin_fail(tmpdir):
    yield fake_executable(tmpdir, 1)


@pytest.fixture
def profile(profile_manager):
    yield profile_manager.create_profile("profile", {"subnets": ["10.0.0.0/24"]})


@pytest.fixture
def pid_file(profile, sessions_dir):
    yield sessions_dir / "profile.pid"


class TestManager:
    def test_default_paths(self):
        """A default config path is set if not specified."""
        assert Manager().config_path == DEFAULT_CONFIG_PATH

    def test_paths(self, profile_manager, config_dir, sessions_dir):
        """The config and sessions are set in the Manager."""
        assert profile_manager.config_path == config_dir
        assert profile_manager.sessions_path == sessions_dir

    def test_load_config_create_dirs(self, profile_manager, config_dir, sessions_dir):
        """Manager.load_config creates config directories."""
        config_dir.rmdir()
        sessions_dir.rmdir()
        profile_manager.load_config()
        assert config_dir.is_dir()
        assert sessions_dir.is_dir()

    def test_load_profiles(self, profile_manager, profiles_file):
        """Manager.load_config loads the profiles."""
        profiles = {"profile": {"subnets": ["10.0.0.0/16"]}}
        profiles_file.write_text(yaml.dump(profiles))
        profile_manager.load_config()
        assert list(profile_manager.get_profiles()) == ["profile"]

    def test_create_profile(self, profile_manager, profiles_file):
        """Manager.create_profile adds a profile with specified details."""
        profile_manager.create_profile("profile", {"subnets": ["10.0.0.0/24"]})
        profiles = yaml.safe_load(profiles_file.read_text())
        assert profiles == {"profile": {"subnets": ["10.0.0.0/24"]}}

    def test_create_profile_in_use(self, profile_manager):
        """Manager.create_profile raises an error if profile name is in use."""
        profile_manager.create_profile("profile", {"subnets": ["10.0.0.0/24"]})
        with pytest.raises(ManagerProfileError):
            profile_manager.create_profile("profile", {"subnets": ["10.0.0.0/16"]})

    @pytest.mark.parametrize(
        "details,message",
        [
            (
                {"subnets": ["1.2.3.0/24"], "wrong": "params"},
                "Invalid profile config 'wrong'",
            ),
            ({"dns": True}, "Profile missing 'subnets' config"),
        ],
    )
    def test_create_profile_invalid_details(self, profile_manager, details, message):
        """Manager.create_profile raises an error on invalid profile info."""
        with pytest.raises(ManagerProfileError) as error:
            profile_manager.create_profile("profile", details)
        assert str(error.value) == message

    def test_remove_profile(self, profile_manager, profile, profiles_file):
        """Manager.remove_profile removes the specified profile."""
        profile_manager.remove_profile("profile")
        config = yaml.safe_load(profiles_file.read_text())
        assert config == {}

    def test_remove_profile_unknown(self, profile_manager):
        """Manager.remove_profile raises an error if name is unknown."""
        with pytest.raises(ManagerProfileError):
            profile_manager.remove_profile("unknown")

    def test_get_profiles(self, profile_manager):
        """Manager.get_profiles returns defined profiles."""
        profile_manager.create_profile("profile1", {"subnets": ["10.0.0.0/24"]})
        profile_manager.create_profile("profile2", {"subnets": ["192.168.0.0/16"]})
        profile_manager.get_profiles() == {
            "profile1": Profile(["10.0.0.0/24"]),
            "profile2": Profile(["192.168.0.0/16"]),
        }

    def test_get_profile(self, profile_manager):
        """Manager.get_profile returns a profile."""
        config = {"subnets": ["10.0.0.0/24"]}
        profile_manager.create_profile("profile", config)
        profile = profile_manager.get_profile("profile")
        assert profile == Profile(**config)

    def test_get_profile_unknown(self, profile_manager):
        """Manager.get_profile raises an error if the name is unknown."""
        with pytest.raises(ManagerProfileError):
            profile_manager.get_profile("unknown")

    def test_start_profile(self, profile_manager, profile, sessions_dir, bin_succeed):
        """Manager.start_profile starts a profile."""
        profile_manager._get_executable = lambda: str(bin_succeed)

        profile_manager.start_profile("profile")
        cmdline = (bin_succeed.parent / "cmdline").read_text()
        assert cmdline == (
            "10.0.0.0/24 --daemon --pidfile {}/profile.pid\n".format(sessions_dir)
        )

    def test_start_profile_extra_args(
        self, profile_manager, profile, sessions_dir, bin_succeed
    ):
        """Manager.start_profile can add extra arguments to command line."""
        profile_manager._get_executable = lambda: str(bin_succeed)

        profile_manager.start_profile("profile", extra_args=["--extra1", "--extra2"])
        cmdline = (bin_succeed.parent / "cmdline").read_text()
        assert cmdline == (
            "10.0.0.0/24 --daemon --pidfile {}/profile.pid --extra1 --extra2\n".format(
                sessions_dir
            )
        )

    def test_start_profile_fail(self, profile_manager, profile, bin_fail):
        """An error is raised if starting a profile fails."""
        profile_manager._get_executable = lambda: str(bin_fail)
        with pytest.raises(ManagerProfileError) as err:
            profile_manager.start_profile("profile")
        assert str(err.value) == "Profile failed to start: stderr message"

    def test_start_profile_executable_not_found(self, profile_manager, profile):
        """Profile start raises an error if executable is not found."""
        profile_manager._get_executable = lambda: "/not/here"
        with pytest.raises(ManagerProfileError):
            profile_manager.start_profile("profile")

    def test_start_profile_unknown(self, profile_manager):
        """Trying to start an unknown profile raises an error."""
        with pytest.raises(ManagerProfileError):
            profile_manager.start_profile("unknown")

    def test_start_profile_running(self, profile_manager, profile):
        """Trying to start a running profile raises an error."""
        profile_manager.is_running = lambda name: True
        with pytest.raises(ManagerProfileError):
            profile_manager.start_profile("profile")

    def test_stop_profile(self, mocker, profile_manager, pid_file):
        """Manager.stop_profile stops a running profile."""
        mock_kill_and_wait = mocker.patch("sshoot.manager.kill_and_wait")
        pid_file.write_text("100\n")
        profile_manager.is_running = lambda name: True
        profile_manager.stop_profile("profile")
        mock_kill_and_wait.assert_called_once_with(100)

    def test_stop_profile_unknown(self, profile_manager):
        """Trying to stop an unknown profile raises an error."""
        with pytest.raises(ManagerProfileError):
            profile_manager.stop_profile("unknown")

    def test_stop_profile_invalid_pidfile(self, profile_manager, pid_file):
        """If pidfile contains invalid data, stopping raises an error."""
        pid_file.write_text("garbage")
        with pytest.raises(ManagerProfileError):
            profile_manager.stop_profile("profile")

    def test_stop_profile_process_not_found(self, mocker, profile_manager, pid_file):
        """If the process fails to stop an error is raised."""
        pid_file.write_text("100\n")

        mock_kill_and_wait = mocker.patch("sshoot.manager.kill_and_wait")
        mock_kill_and_wait.side_effect = ProcessLookupError

        profile_manager.is_running = lambda name: True
        with pytest.raises(ManagerProfileError) as err:
            profile_manager.stop_profile("profile")
        assert "Failed to stop profile" in str(err.value)
        mock_kill_and_wait.assert_called_once_with(100)

    def test_restart_profile(
        self, mocker, profile_manager, pid_file, profile, sessions_dir, bin_succeed
    ):
        """Manage.restart_profile restarts a running profile."""
        profile_manager._get_executable = lambda: str(bin_succeed)
        mocker.patch.object(profile_manager, "is_running").side_effect = [
            True,
            True,
            False,
        ]
        mock_kill_and_wait = mocker.patch("sshoot.manager.kill_and_wait")
        pid_file.write_text("100\n")

        profile_manager.restart_profile("profile")

        mock_kill_and_wait.assert_called_once_with(100)
        cmdline = (bin_succeed.parent / "cmdline").read_text()
        assert cmdline == (
            "10.0.0.0/24 --daemon --pidfile {}/profile.pid\n".format(sessions_dir)
        )

    def test_get_pidfile(self, profile_manager, pid_file):
        """Manager._get_pidfile returns the pidfile path for a session."""
        assert profile_manager._get_pidfile("profile") == pid_file

    def test_is_running(self, profile_manager, pid_file):
        """If the process is present, the profile is running."""
        pid_file.write_text("{}\n".format(os.getpid()))
        assert profile_manager.is_running("profile")

    def test_is_running_no_pidfile(self, profile_manager):
        """If the pidfile is not found, the profile is not running."""
        assert not profile_manager.is_running("not-here")

    def test_is_running_pidfile_empty(self, profile_manager, pid_file):
        """If the pidfile is empty, the profile is not running."""
        pid_file.write_text("")
        assert not profile_manager.is_running("profile")

    def test_is_running_pidfile_no_integer(self, profile_manager, pid_file):
        """If the pid is not an integer, the profile is not running."""
        pid_file.write_text("foo\n")
        assert not profile_manager.is_running("profile")

    def test_is_running_pidfile_no_process(self, profile_manager, pid_file):
        """If no process is present, the profile is not running."""
        pid_file.write_text("-100\n")
        assert not profile_manager.is_running("profile")
        # The stale pidfile is deleted.
        assert not pid_file.exists()

    def test_get_cmdline(self, profile_manager, pid_file):
        """Manager.get_cmdline returns the command line for the profile."""
        assert profile_manager.get_cmdline("profile") == [
            "sshuttle",
            "10.0.0.0/24",
            "--daemon",
            "--pidfile",
            str(pid_file),
        ]

    def test_get_cmdline_extra_args(self, profile_manager, pid_file):
        """Manager.get_cmdline adds passed extra arguments to command line."""
        cmdline = profile_manager.get_cmdline(
            "profile", extra_args=["--extra1", "--extra2"]
        )
        assert cmdline == [
            "sshuttle",
            "10.0.0.0/24",
            "--daemon",
            "--pidfile",
            str(pid_file),
            "--extra1",
            "--extra2",
        ]

    def test_get_cmdline_executable(self, profile_manager, pid_file):
        """Manager.get_cmdline uses the configured executable."""
        profile_manager._get_executable = lambda: "/foo/sshuttle"
        assert profile_manager.get_cmdline("profile") == [
            "/foo/sshuttle",
            "10.0.0.0/24",
            "--daemon",
            "--pidfile",
            str(pid_file),
        ]


@pytest.fixture
def mock_kill(mocker):
    yield mocker.patch("sshoot.manager.os.kill")


@pytest.fixture
def mock_sleep(mocker):
    yield mocker.patch("sshoot.manager.time.sleep")


class TestKillAndWait:
    def test_return_if_process_dead(self, mock_kill, mock_sleep):
        """No erorr is reported if the process is not found."""
        mock_kill.side_effect = ProcessLookupError
        kill_and_wait(123)
        mock_kill.assert_called_once_with(123, signal.SIGTERM)
        mock_sleep.assert_not_called()

    def test_retry(self, mocker, mock_kill, mock_sleep):
        """The kill call is retried if process isn't dead yet."""
        mock_kill.side_effect = [None, None, ProcessLookupError]
        kill_and_wait(123)
        assert mock_kill.mock_calls == [mocker.call(123, signal.SIGTERM)] * 3
        assert mock_sleep.mock_calls == [mocker.call(0.2)] * 2

    def test_retry_term_and_killl(self, mocker, mock_kill, mock_sleep):
        """The kill is performed with SIGKILL after SIGTERM."""
        mock_kill.side_effect = [None] * 12 + [ProcessLookupError]
        kill_and_wait(123)
        mock_kill
        assert (
            mock_kill.mock_calls
            == [mocker.call(123, signal.SIGTERM)] * 11
            + [mocker.call(123, signal.SIGKILL)] * 2
        )

    def test_raises_eventually(self, mocker, mock_kill, mock_sleep):
        """If the process doesn't die, an error is raised."""
        with pytest.raises(ProcessKillFail) as error:
            kill_and_wait(123)
        assert error.value.pid == 123
        assert (
            mock_kill.mock_calls
            == [mocker.call(123, signal.SIGTERM)] * 11
            + [mocker.call(123, signal.SIGKILL)] * 6
        )

    def test_no_retry_on_error(self, mock_kill, mock_sleep):
        """If the kill call fails, the error is raised."""
        mock_kill.side_effect = PermissionError
        with pytest.raises(PermissionError):
            kill_and_wait(123)
        mock_kill.assert_called_once_with(123, signal.SIGTERM)
        mock_sleep.assert_not_called()


class TestGetRundir:
    def test_rundir_path(self):
        """get_rundir returns a user-specific tempdir path."""
        rundir_path = Path(gettempdir()) / "foo-{}".format(getuser())
        assert get_rundir("foo") == rundir_path
