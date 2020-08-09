from io import StringIO
from textwrap import dedent

import pytest
import yaml

from ..config import yaml_dump
from ..profile import Profile


class TestYamlDump:
    def test_dump_to_string(self):
        """The method returns YAML data as a string by default."""
        data = {"foo": "bar", "baz": [1, 2]}
        result = yaml_dump(data)
        assert yaml.safe_load(stream=StringIO(result)) == data

    def test_dump_to_file(self):
        """The method dumps YAML data to the specified file."""
        data = {"foo": "bar", "baz": [1, 2]}
        fh = StringIO()
        result = yaml_dump(data, fh=fh)
        fh.seek(0)
        assert result is None
        assert yaml.safe_load(stream=fh) == data


class TestConfig:
    def test_add_profile(self, config):
        """Profiles can be added to the config."""
        profiles = {
            "profile1": Profile(["10.0.0.0/24"]),
            "profile2": Profile(["192.168.0.0/16"]),
        }
        for name, profile in profiles.items():
            config.add_profile(name, profile)
        assert config.profiles == profiles

    def test_add_profile_name_present(self, config):
        """An exception is raised if the profile name is already used."""
        config.add_profile("profile", Profile(["10.0.0.0/24"]))
        with pytest.raises(KeyError):
            config.add_profile("profile", Profile(["192.168.0.0/16"]))

    def test_remove_profile(self, config):
        """Profiles can be removed to the config."""
        profiles = {
            "profile1": Profile(["10.0.0.0/24"]),
            "profile2": Profile(["192.168.0.0/16"]),
        }
        for name, profile in profiles.items():
            config.add_profile(name, profile)
        config.remove_profile("profile1")
        assert list(config.profiles), ["profile2"]

    def test_remove_profile_not_present(self, config):
        """An exception is raised if the profile name is not known."""
        with pytest.raises(KeyError):
            config.remove_profile("profile")

    def test_load_from_file(self, config, profiles_file):
        """The config is loaded from file."""
        profiles = {"profile": {"subnets": ["10.0.0.0/24"], "auto-nets": True}}
        profiles_file.write_text(yaml.dump(profiles))
        config.load()
        profile = config.profiles["profile"]
        assert profile.subnets == ["10.0.0.0/24"]
        assert profile.auto_nets

    def test_load_missing_file(self, config):
        """If no config files are found, config is empty."""
        config.load()
        assert config.profiles == {}
        assert config.config == {}

    def test_load_config_options(self, config, config_file):
        """Only known config options are loaded from config file."""
        config_data = {"executable": "/usr/bin/shuttle", "other-conf": "no"}
        config_file.write_text(yaml.dump(config_data))
        config.load()
        assert config.config == {"executable": "/usr/bin/shuttle"}

    def test_load_profiles(self, config, profiles_file):
        """The 'profiles' config field is loaded from the config file."""
        profiles = {
            "profile1": {"subnets": ["10.0.0.0/24"]},
            "profile2": {"subnets": ["192.168.0.0/16"]},
        }
        profiles_file.write_text(yaml.dump(profiles))
        config.load()
        expected = {name: Profile(**config) for name, config in profiles.items()}
        assert config.profiles == expected

    def test_save_profiles(self, config, profiles_file):
        """Profiles are saved to file."""
        profiles = {
            "profile1": {"subnets": ["10.0.0.0/24"], "remote": "hostname1"},
            "profile2": {"subnets": ["192.168.0.0/16"], "remote": "hostname2"},
        }
        config.load()
        for name, conf in profiles.items():
            config.add_profile(name, Profile(**conf))
        config.save()
        config = yaml.safe_load(profiles_file.read_text())
        assert config == profiles

    def test_save_from_file(self, config, profiles_file):
        """The config is saved to file."""
        config.add_profile("profile", Profile(["10.0.0.0/24"], auto_nets=True))
        config.save()

        config = dedent(
            """\
            profile:
              auto-nets: true
              subnets:
              - 10.0.0.0/24
            """
        )
        content = profiles_file.read_text()
        assert content == config
