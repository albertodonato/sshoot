#
# This file is part of sshoot.
#
# sshoot is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# sshoot is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with sshoot.  If not, see <http://www.gnu.org/licenses/>.

from unittest.mock import patch
from collections import namedtuple

from fixtures import TestWithFixtures, TempDir

from ..manager import Manager
from ..autocomplete import profile_completer


FakeParsedArgs = namedtuple('FakeParsedArgs', ['config'])


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
        '''The autocomplete function returns names that match the prefix.'''
        self.assertCountEqual(
            ['bar', 'baz'], profile_completer('b', self.fake_args))

    @patch('sshoot.autocomplete.Manager')
    def test_complete_filter_running(self, mock_manager):
        '''The autocomplete function returns names that match the prefix.'''
        mock_manager.return_value = self.manager
        self.manager.is_running = lambda name: name != 'bar'
        self.assertCountEqual(
            ['foo', 'baz'],
            profile_completer('', self.fake_args, running=True))

    @patch('sshoot.autocomplete.Manager')
    def test_complete_filter_not_running(self, mock_manager):
        '''The autocomplete function returns names that match the prefix.'''
        mock_manager.return_value = self.manager
        self.manager.is_running = lambda name: name != 'bar'
        self.assertCountEqual(
            ['bar'], profile_completer('', self.fake_args, running=False))
