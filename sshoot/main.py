"""Command-line interface to handle sshuttle VPN sessions."""

import sys
import os
import shutil
from functools import partial
from argparse import ArgumentParser

from argcomplete import autocomplete

from . import __version__
from .manager import (
    Manager,
    ManagerProfileError,
    DEFAULT_CONFIG_PATH)
from .listing import (
    ProfileListing,
    profile_details)
from .autocomplete import (
    complete_argument,
    profile_completer)


class Sshoot:
    """Manage multiple sshuttle VPN sessions."""

    def __call__(self):
        args = self._get_parser().parse_args()
        # backwards-compatible config lookup
        self._check_update_config_path(args.config)

        try:
            manager = Manager(config_path=args.config)
            manager.load_config()
        except IOError as error:
            self._exit(message=str(error), code=3)
        action = args.action.replace('-', '_')
        method = getattr(self, 'action_' + action)
        try:
            return method(manager, args)
        except ManagerProfileError as error:
            self._exit(message=str(error), code=2)

    def action_list(self, manager, args):
        """Print out the list of profiles as a table."""
        listing = ProfileListing(manager)
        print(listing.get_output(args.format, verbose=args.verbose), end='')

    def action_show(self, manager, args):
        """Show details on a profile."""
        print(profile_details(manager, args.name))

    def action_create(self, manager, args):
        """Create a new profile."""
        manager.create_profile(args.name, args.__dict__)

    def action_delete(self, manager, args):
        """Delete profile with the given name."""
        manager.remove_profile(args.name)

    def action_start(self, manager, args):
        """Start sshuttle for the specified profile."""
        manager.start_profile(args.name, extra_args=args.args)
        print('Profile started')

    def action_stop(self, manager, args):
        """Stop sshuttle for the specified profile."""
        manager.stop_profile(args.name)
        print('Profile stopped')

    def action_is_running(self, manager, args):
        """Return whether the specified profile is running."""
        # raise an error if profile is unknown
        manager.get_profile(args.name)
        retval = 0 if manager.is_running(args.name) else 1
        self._exit(code=retval)

    def action_get_command(self, manager, args):
        """Print the sshuttle command for the specified profile."""
        cmdline = manager.get_cmdline(args.name)
        print(' '.join(cmdline))

    def _get_parser(self):
        """Return a configured argparse.ArgumentParse instance."""
        parser = ArgumentParser(description=self.__doc__)
        parser.add_argument(
            '-V', '--version', action='version',
            version='%(prog)s {}'.format(__version__))
        parser.add_argument(
            '-C', '--config', default=DEFAULT_CONFIG_PATH,
            help='configuration directory (default: %(default)s)')
        subparsers = parser.add_subparsers(
            metavar='ACTION', dest='action', help='action to perform')
        subparsers.required = True

        # List profiles
        list_parser = subparsers.add_parser(
            'list', help='list defined profiles')
        list_parser.add_argument(
            '-v', '--verbose', action='store_true',
            help='verbose listing')
        list_parser.add_argument(
            '-f', '--format', choices=ProfileListing.supported_formats(),
            default='table',
            help='listing format (default %(default)s)')

        # Show profile
        show_parser = subparsers.add_parser(
            'show', help='show profile configuration')
        complete_argument(
            show_parser.add_argument('name', help='profile name'),
            profile_completer)

        # Add profile
        create_parser = subparsers.add_parser(
            'create', help='define a new profile')
        create_parser.add_argument('name', help='profile name')
        create_parser.add_argument(
            'subnets', nargs='+', help='subnets to route over the VPN')
        create_parser.add_argument(
            '-r', '--remote', help='remote host to connect to')
        create_parser.add_argument(
            '-H', '--auto-hosts', action='store_true',
            help='automatically update /etc/hosts with hosts from VPN')
        create_parser.add_argument(
            '-N', '--auto-nets', action='store_true',
            help='automatically route additional nets from server')
        create_parser.add_argument(
            '-d', '--dns', action='store_true',
            help='forward DNS queries through the VPN')
        create_parser.add_argument(
            '-x', '--exclude-subnets', nargs='+',
            help='exclude subnets from VPN forward')
        create_parser.add_argument(
            '-S', '--seed-hosts', nargs='+',
            help='comma-separated list of hosts to seed to auto-hosts')
        create_parser.add_argument(
            '--extra-opts', type=str.split,
            help='extra options to pass to sshuttle command line')

        # Remove profile
        delete_parser = subparsers.add_parser(
            'delete', help='delete an existing profile')
        complete_argument(
            delete_parser.add_argument(
                'name', help='name of the profile to remove'),
            profile_completer)

        # Start profile
        start_parser = subparsers.add_parser(
            'start', help='start a VPN session for a profile')
        complete_argument(
            start_parser.add_argument(
                'name', help='name of the profile to start'),
            partial(profile_completer, running=False))
        start_parser.add_argument(
            'args', nargs='*',
            help='Additional arguments passed to sshuttle command line.')

        # Stop profile
        stop_parser = subparsers.add_parser(
            'stop', help='stop a running VPN session for a profile')
        complete_argument(
            stop_parser.add_argument(
                'name', help='name of the profile to stop'),
            partial(profile_completer, running=True))

        # Return whether profile is running
        is_running_parser = subparsers.add_parser(
            'is-running', help='return whether a profile is running')
        complete_argument(
            is_running_parser.add_argument(
                'name', help='name of the profile to query'),
            profile_completer)

        # Get profile command
        get_command_parser = subparsers.add_parser(
            'get-command', help='return the sshuttle command for a profile')
        complete_argument(
            get_command_parser.add_argument(
                'name', help='name of the profile'),
            profile_completer)

        # Setup autocompletion
        autocomplete(parser)
        return parser

    def _check_update_config_path(self, config):
        """Move config to the new path if the old one is found."""
        old_config_path = os.path.expanduser(os.path.join('~', '.sshoot'))
        if config != DEFAULT_CONFIG_PATH:
            return

        need_config_path_update = (
            os.path.exists(old_config_path) and
            not os.path.exists(DEFAULT_CONFIG_PATH))
        if need_config_path_update:
            shutil.move(old_config_path, DEFAULT_CONFIG_PATH)
            sys.stderr.write(
                'NOTICE: configuration tree moved from {} to {}\n'.format(
                    old_config_path, DEFAULT_CONFIG_PATH))

    def _exit(self, message=None, code=1):
        """Terminate with the specified error and code ."""
        if message:
            sys.stderr.write('{}\n'.format(message))
        sys.exit(code)


sshoot = Sshoot()
