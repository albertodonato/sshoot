import csv
from io import StringIO
import json

import pytest
import yaml

from ..listing import (
    InvalidFormat,
    profile_details,
    ProfileListing,
)


@pytest.fixture
def active_profiles(profile_manager):
    active_profiles = []
    profile_manager.is_running = lambda name: name in active_profiles
    yield active_profiles


class TestProfileListing:
    def test_supported_formats(self):
        """supported_formats returns a list with supported formats."""
        assert ProfileListing.supported_formats() == ["csv", "json", "table", "yaml"]

    def test_get_output_unsupported_format(self, profile_manager):
        """get_output raises an error if an unsupported format is passed."""
        with pytest.raises(InvalidFormat):
            ProfileListing(profile_manager).get_output("unknown")

    def test_get_output_table(self, profile_manager, active_profiles):
        """Profiles can be listed as a table."""
        profile_manager.create_profile("profile1", {"subnets": ["10.0.0.0/24"]})
        profile_manager.create_profile("profile2", {"subnets": ["192.168.0.0/16"]})
        active_profiles.append("profile2")
        output = ProfileListing(profile_manager).get_output("table")
        assert "   profile1               10.0.0.0/24" in output
        assert "*  profile2               192.168.0.0/16" in output

    def test_get_output_table_verbose(self, profile_manager, active_profiles):
        """Tabular output can be verbose."""
        profile_manager.create_profile(
            "profile1", {"subnets": ["10.0.0.0/24"], "auto_hosts": True}
        )
        active_profiles.append("profile2")
        output = ProfileListing(profile_manager).get_output("table", verbose=True)
        assert (
            "Name      Remote host  Subnets      Auto hosts  Auto nets"
            "  DNS forward  Exclude subnets  Seed hosts  Extra options" in output
        )
        assert (
            "profile1               10.0.0.0/24  True        False      False" in output
        )

    def test_get_output_csv(self, profile_manager, active_profiles):
        """Profiles can be listed as CSV."""
        profile_manager.create_profile("profile1", {"subnets": ["10.0.0.0/24"]})
        profile_manager.create_profile("profile2", {"subnets": ["192.168.0.0/16"]})
        active_profiles.append("profile2")
        output = ProfileListing(profile_manager).get_output("csv")
        reader = csv.reader(StringIO(output))
        assert sorted(reader) == [
            [
                "Name",
                "Status",
                "Remote host",
                "Subnets",
                "Auto hosts",
                "Auto nets",
                "DNS forward",
                "Exclude subnets",
                "Seed hosts",
                "Extra options",
            ],
            [
                "profile1",
                "STOPPED",
                "",
                "['10.0.0.0/24']",
                "False",
                "False",
                "False",
                "",
                "",
                "",
            ],
            [
                "profile2",
                "ACTIVE",
                "",
                "['192.168.0.0/16']",
                "False",
                "False",
                "False",
                "",
                "",
                "",
            ],
        ]

    def test_get_output_json(self, profile_manager, active_profiles):
        """Profiles can be listed as JSON."""
        profile_manager.create_profile("profile1", {"subnets": ["10.0.0.0/24"]})
        profile_manager.create_profile(
            "profile2", {"subnets": ["192.168.0.0/16"], "auto-hosts": True}
        )
        active_profiles.append("profile2")
        output = ProfileListing(profile_manager).get_output("json")
        data = json.loads(output)
        assert data == {
            "profile1": {"subnets": ["10.0.0.0/24"]},
            "profile2": {"subnets": ["192.168.0.0/16"], "auto-hosts": True},
        }

    def test_get_output_yaml(self, profile_manager, active_profiles):
        """Profiles can be listed as YAML."""
        profile_manager.create_profile("profile1", {"subnets": ["10.0.0.0/24"]})
        profile_manager.create_profile(
            "profile2", {"subnets": ["192.168.0.0/16"], "auto-hosts": True}
        )
        active_profiles.append("profile2")
        output = ProfileListing(profile_manager).get_output("yaml")
        data = yaml.safe_load(output)
        assert data == {
            "profile1": {"subnets": ["10.0.0.0/24"]},
            "profile2": {"subnets": ["192.168.0.0/16"], "auto-hosts": True},
        }


class TestProfileDetails:
    def test_details(self, profile_manager):
        """profile_details returns a string with profile details."""
        profile_manager.create_profile("profile", {"subnets": ["10.0.0.0/24"]})
        output = profile_details(profile_manager, "profile")
        assert "Name:             profile" in output
        assert "Subnets:          10.0.0.0/24" in output
        assert "Status:           STOPPED" in output

    def test_active(self, profile_manager, active_profiles):
        """profile_details shows if the profile is active."""
        profile_manager.create_profile("profile", {"subnets": ["10.0.0.0/24"]})
        active_profiles.append("profile")
        output = profile_details(profile_manager, "profile")
        assert "Status:           ACTIVE" in output
