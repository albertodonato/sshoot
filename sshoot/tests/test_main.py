from io import StringIO

import pytest

from .. import main
from ..manager import ManagerProfileError


@pytest.fixture
def stdout():
    yield StringIO()


@pytest.fixture
def stderr():
    yield StringIO()


@pytest.fixture
def manager(mocker):
    yield mocker.MagicMock()


@pytest.fixture
def script(mocker, stdout, stderr, manager):
    mocker.patch.object(main, "Manager").return_value = manager
    script = main.Sshoot(stdout=stdout, stderr=stderr)
    yield script


@pytest.fixture
def sys_exit(mocker):
    return mocker.patch("sys.exit")


class TestSshoot:
    def test_load_error(self, script, manager, stderr, sys_exit):
        """If config load fails, an error is returned."""
        manager.load_config.side_effect = IOError("fail!")
        script(["start", "profile1"])
        sys_exit.assert_called_once_with(3)
        assert stderr.getvalue() == "fail!\n"

    def test_profile_error(self, script, manager, stderr, sys_exit):
        """If profile load fails, an error is returned."""
        manager.get_profile.side_effect = ManagerProfileError("not found")
        script(["show", "profile1"])
        sys_exit.assert_called_once_with(2)
        assert stderr.getvalue() == "not found\n"

    def test_create(self, script, manager):
        """A profile can be added."""
        script(
            [
                "create",
                "profile1",
                "-r",
                "example.net",
                "10.10.0.0/16",
                "192.168.1.0/24",
            ]
        )
        manager.create_profile.assert_called_once_with(
            "profile1",
            {
                "subnets": ["10.10.0.0/16", "192.168.1.0/24"],
                "remote": "example.net",
                "auto_hosts": False,
                "auto_nets": False,
                "dns": False,
                "exclude_subnets": None,
                "seed_hosts": None,
                "extra_opts": None,
            },
        )

    def test_show(self, script, manager, stdout):
        """Profile details can be viewed."""
        script(["show", "profile1"])
        manager.get_profile.assert_called_once_with("profile1")
        assert "Name:             profile1" in stdout.getvalue()

    def test_list(self, script, stdout):
        """Profile list can be viewed."""
        script(["list", "--format", "json"])
        assert stdout.getvalue() == "{}"

    def test_remove(self, script, manager):
        """A profile can be removed."""
        script(["delete", "profile1"])
        manager.remove_profile.assert_called_once_with("profile1")

    def test_start(self, stdout, script, manager):
        """A profile can be started."""
        script(["start", "profile1", "--", "--syslog"])
        manager.start_profile.assert_called_once_with(
            "profile1", extra_args=["--syslog"]
        )
        assert stdout.getvalue() == "Profile started\n"

    def test_stop(self, stdout, script, manager):
        """A profile can be stopped."""
        script(["stop", "profile1"])
        manager.stop_profile.assert_called_once_with("profile1")
        assert stdout.getvalue() == "Profile stopped\n"

    def test_restart(self, stdout, script, manager):
        """A profile can be restarted."""
        script(["restart", "profile1", "--", "--syslog"])
        manager.restart_profile.assert_called_once_with(
            "profile1", extra_args=["--syslog"]
        )
        assert stdout.getvalue() == "Profile restarted\n"

    @pytest.mark.parametrize("running,exit_value", [(True, 0), (False, 1)])
    def test_is_running(self, mocker, sys_exit, script, manager, running, exit_value):
        """It's possible to check if a profile is running."""
        manager.is_running.return_value = running
        script(["is-running", "profile1"])
        sys_exit.assert_called_once_with(exit_value)

    def test_get_command(self, stdout, script, manager):
        """It's possible to get the sshuttle commandline."""
        manager.get_cmdline.return_value = ["sshuttle", "-r", "example.net"]
        script(["get-command", "profile1"])
        manager.get_cmdline.assert_called_once_with("profile1")
        assert stdout.getvalue() == "sshuttle -r example.net\n"
