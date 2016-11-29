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

'''Shell completion helpers.'''

from .manager import Manager


def complete_argument(argument, completer):
    '''wrapper for setting up argument completer.'''
    argument.completer = completer
    return argument


def profile_completer(prefix, parsed_args, running=None, **kwargs):
    '''Autocomplete helper for profile names.

    Parameters:
        - running: filter profiles that are running or not (by default no
          filter is applied).
    '''
    manager = Manager(config_path=parsed_args.config)
    manager.load_config()
    for name in manager.get_profiles().keys():
        if not name.startswith(prefix):
            continue
        if running is None or manager.is_running(name) == running:
            # Either no filter is set or it matches the profile status
            yield name
