import pytest

from ..profile import (
    Profile,
    ProfileError,
)


@pytest.fixture
def profile():
    yield Profile(["1.1.1.0/24", "10.10.0.0/16"])


class TestProfile:
    def test_cmdline(self, profile):
        """Profile.cmdline() return the sshuttle cmdline for the config."""
        assert profile.cmdline() == ["sshuttle", "1.1.1.0/24", "10.10.0.0/16"]

    def test_cmdline_with_options(self, profile):
        """Profile.cmdline() return the sshuttle cmdline for the config."""
        profile.remote = "1.2.3.4"
        profile.auto_hosts = True
        profile.auto_nets = True
        profile.dns = True
        profile.cmdline() == [
            "sshuttle",
            "1.1.1.0/24",
            "10.10.0.0/16",
            "--remote=1.2.3.4",
            "--auto-hosts",
            "--auto-nets",
            "--dns",
        ]

    def test_cmdline_exclude_subnets(self, profile):
        """Profile.cmdline() includes excluded subnets in the cmdline."""
        profile.exclude_subnets = ["10.20.0.0/16", "10.30.0.0/16"]
        profile.cmdline() == [
            "sshuttle",
            "1.1.1.0/24",
            "10.10.0.0/16",
            "--exclude=10.20.0.0/16",
            "--exclude=10.30.0.0/16",
        ]

    def test_cmdline_seed_hosts(self, profile):
        """Profile.cmdline() includes seeded hosts in the cmdline."""
        profile.seed_hosts = ["10.1.2.3", "10.4.5.6"]
        profile.cmdline(), [
            "sshuttle",
            "1.1.1.0/24",
            "10.10.0.0/16",
            "--seed-hosts=10.1.2.3,10.4.5.6",
        ]

    def test_cmdline_with_profile_extra_opts(self, profile):
        """Profile.cmdline() return the sshuttle cmdline with extra options."""
        profile.extra_opts = ["--verbose", "--daemon"]
        assert profile.cmdline() == [
            "sshuttle",
            "1.1.1.0/24",
            "10.10.0.0/16",
            "--verbose",
            "--daemon",
        ]

    def test_cmdline_with_extra_opts(self, profile):
        """Profile.cmdline() includes extra options."""
        profile.cmdline(extra_opts=["--verbose", "--daemon"]), [
            "sshuttle",
            "1.1.1.0/24",
            "10.10.0.0/16",
            "--verbose",
            "--daemon",
        ]

    def test_cmdline_with_executable(self, profile):
        """Profile.cmdline() uses the specified executable."""
        assert profile.cmdline(executable="/bin/foo") == [
            "/bin/foo",
            "1.1.1.0/24",
            "10.10.0.0/16",
        ]

    def test_config(self, profile):
        """Profile.config() returns a dict with the profile config."""
        profile.remote = "1.2.3.4"
        profile.dns = True
        profile.auto_hosts = True
        assert profile.config() == {
            "auto-hosts": True,
            "remote": "1.2.3.4",
            "dns": True,
            "subnets": ["1.1.1.0/24", "10.10.0.0/16"],
        }

    def test_from_config(self, profile):
        """Profile.from-config builds a profile from a config."""
        assert Profile.from_config(profile.config()) == profile

    def test_from_config_missing_subnets(self):
        """An error is raised if config is missing the 'subnets' key."""
        with pytest.raises(ProfileError) as error:
            Profile.from_config({})
        assert str(error.value) == "Profile missing 'subnets' config"

    def test_update(self, profile):
        """A Profile can be updated."""
        profile.update({"auto-nets": True, "subnets": ["1.2.3.0/24"]})
        assert profile.auto_nets
        assert profile.subnets == ["1.2.3.0/24"]

    def test_update_invalid_config(self, profile):
        """An error is raised if invalid key is passed to Profile.update()."""
        with pytest.raises(ProfileError) as error:
            profile.update({"unknown": "key"})
        assert str(error.value) == "Invalid profile config 'unknown'"
