from unittest import TestCase
from unittest.mock import patch
from collections import namedtuple

from fixtures import TestWithFixtures, TempDir

from ..manager import Manager
from ..autocomplete import complete_argument, profile_completer


FakeParsedArgs = namedtuple('FakeParsedArgs', ['config'])


class CompleteArgumentTests(TestCase):

    def test_complete_arguments(self):
        """complete_arguments attaches a completer to the argument."""

        class FakeArgument:
            completer = None

        fake_argument = FakeArgument()
        fake_completer = object()
        complete_argument(fake_argument, fake_completer)
        self.assertIs(fake_argument.completer, fake_completer)


class ProfileCompleterTests(TestWithFixtures):

    def setUp(self):
        super().setUp()
        self.config_path = self.useFixture(TempDir()).path
        self.manager = Manager(config_path=self.config_path)
        self.manager.create_profile('foo', {'subnets': ['10.1.0.0/16']})
        self.manager.create_profile('bar', {'subnets': ['10.2.0.0/16']})
        self.manager.create_profile('baz', {'subnets': ['10.2.0.0/16']})

        self.fake_args = FakeParsedArgs(self.config_path)

    def test_complete_filter_prefix(self):
        """The autocomplete function returns names that match the prefix."""
        self.assertCountEqual(
            ['bar', 'baz'], profile_completer('b', self.fake_args))

    @patch('sshoot.autocomplete.Manager')
    def test_complete_filter_running(self, mock_manager):
        """The autocomplete function returns names that match the prefix."""
        mock_manager.return_value = self.manager
        self.manager.is_running = lambda name: name != 'bar'
        self.assertCountEqual(
            ['foo', 'baz'],
            profile_completer('', self.fake_args, running=True))

    @patch('sshoot.autocomplete.Manager')
    def test_complete_filter_not_running(self, mock_manager):
        """The autocomplete function returns names that match the prefix."""
        mock_manager.return_value = self.manager
        self.manager.is_running = lambda name: name != 'bar'
        self.assertCountEqual(
            ['bar'], profile_completer('', self.fake_args, running=False))
