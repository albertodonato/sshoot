import pytest

from ..profile import (
    Profile,
    ProfileError,
)


@pytest.fixture
def profile():
    yield Profile(['1.1.1.0/24', '10.10.0.0/16'])


class TestProfile:

    def test_from_dict(self):
        """A Profile can be created from a dict with its attributes."""
        profile = Profile.from_dict(
            {
                'remote': '1.2.3.4',
                'subnets': ['1.1.1.0/24', '10.10.0.0/16'],
                'dns': True,
                'auto_hosts': True
            })
        assert profile.remote == '1.2.3.4'
        assert profile.subnets == ['1.1.1.0/24', '10.10.0.0/16']
        assert profile.dns
        assert profile.auto_hosts
        # Other attributes are set to default
        assert not profile.auto_nets
        assert profile.exclude_subnets is None
        assert profile.seed_hosts is None
        assert profile.extra_opts is None

    def test_from_dict_raise_error(self):
        """If the 'subnets' key is missing in config, an error is raised."""
        with pytest.raises(ProfileError):
            Profile.from_dict({'remote': '1.2.3.4'})

    def test_cmdline(self, profile):
        """Profile.cmdline() return the sshuttle cmdline for the config."""
        assert profile.cmdline() == ['sshuttle', '1.1.1.0/24', '10.10.0.0/16']

    def test_cmdline_with_options(self, profile):
        """Profile.cmdline() return the sshuttle cmdline for the config."""
        profile.remote = '1.2.3.4'
        profile.auto_hosts = True
        profile.auto_nets = True
        profile.dns = True
        profile.cmdline() == [
            'sshuttle', '1.1.1.0/24', '10.10.0.0/16', '--remote=1.2.3.4',
            '--auto-hosts', '--auto-nets', '--dns'
        ]

    def test_cmdline_exclude_subnets(self, profile):
        """Profile.cmdline() includes excluded subnets in the cmdline."""
        profile.exclude_subnets = ['10.20.0.0/16', '10.30.0.0/16']
        profile.cmdline() == [
            'sshuttle', '1.1.1.0/24', '10.10.0.0/16', '--exclude=10.20.0.0/16',
            '--exclude=10.30.0.0/16'
        ]

    def test_cmdline_seed_hosts(self, profile):
        """Profile.cmdline() includes seeded hosts in the cmdline."""
        profile.seed_hosts = ['10.1.2.3', '10.4.5.6']
        profile.cmdline(), [
            'sshuttle', '1.1.1.0/24', '10.10.0.0/16',
            '--seed-hosts=10.1.2.3,10.4.5.6'
        ]

    def test_cmdline_with_profile_extra_opts(self, profile):
        """Profile.cmdline() return the sshuttle cmdline with extra options."""
        profile.extra_opts = ['--verbose', '--daemon']
        assert profile.cmdline() == [
            'sshuttle', '1.1.1.0/24', '10.10.0.0/16', '--verbose', '--daemon'
        ]

    def test_cmdline_with_extra_opts(self, profile):
        """Profile.cmdline() includes extra options."""
        profile.cmdline(extra_opts=['--verbose', '--daemon']), [
            'sshuttle', '1.1.1.0/24', '10.10.0.0/16', '--verbose', '--daemon'
        ]

    def test_cmdline_with_executable(self, profile):
        """Profile.cmdline() uses the specified executable."""
        assert profile.cmdline(executable='/bin/foo') == [
            '/bin/foo', '1.1.1.0/24', '10.10.0.0/16'
        ]

    def test_config(self, profile):
        """Profile.config() returns a dict with the profile config."""
        profile.remote = '1.2.3.4'
        profile.dns = True
        assert profile.config() == {
            'remote': '1.2.3.4',
            'dns': True,
            'subnets': ['1.1.1.0/24', '10.10.0.0/16']
        }

    def test_config_rebuild_profiles(self, profile):
        """Result of Profile.config() can be used build an equal Profile."""
        assert Profile.from_dict(profile.config()) == profile

    def test_eq(self, profile):
        """Profiles can be tested for equality."""
        assert Profile(['1.1.1.0/24', '10.10.0.0/16']) == profile

    def test_eq_false(self, profile):
        """Profiles with different config don't evaluate as equal."""
        other_profile = Profile(['1.1.1.0/24', '10.10.0.0/16'])
        other_profile.auto_hosts = True
        assert other_profile != profile
