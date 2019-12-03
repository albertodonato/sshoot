from argparse import Namespace

import pytest

from ..autocomplete import (
    complete_argument,
    profile_completer,
)


class TestCompleteArgument:
    def test_complete(self):
        """complete_arguments attaches a completer to the argument."""

        class FakeArgument:
            completer = None

        fake_argument = FakeArgument()
        fake_completer = object()
        complete_argument(fake_argument, fake_completer)
        assert fake_argument.completer is fake_completer


@pytest.fixture
def profiles(profile_manager):
    yield [
        profile_manager.create_profile("foo", {"subnets": ["10.1.0.0/16"]}),
        profile_manager.create_profile("bar", {"subnets": ["10.2.0.0/16"]}),
        profile_manager.create_profile("baz", {"subnets": ["10.3.0.0/16"]}),
    ]


@pytest.fixture
def parsed_args(config_dir):
    yield Namespace(config=config_dir)


@pytest.mark.usefixtures("profiles")
class TestProfileCompleter:
    def test_complete_filter_prefix(self, parsed_args):
        """The autocomplete function returns names that match the prefix."""
        assert list(profile_completer("b", parsed_args)) == ["bar", "baz"]

    @pytest.mark.parametrize(
        "running,completions", [(True, ["baz", "foo"]), (False, ["bar"])]
    )
    def test_complete_filter_running(
        self, running, completions, mocker, profile_manager, parsed_args
    ):
        """The autocomplete function returns names based on running status."""
        mock_manager = mocker.patch("sshoot.autocomplete.Manager")
        mock_manager.return_value = profile_manager
        profile_manager.is_running = lambda name: name != "bar"
        returned = list(profile_completer("", parsed_args, running=running))
        assert returned == completions
