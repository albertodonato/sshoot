"""Command-line interface to handle sshuttle VPN sessions."""

import sys
from functools import partial
from argparse import ArgumentParser

from argcomplete import autocomplete
from prettytable import PrettyTable, HEADER

from . import __version__
from .manager import Manager, ManagerProfileError, DEFAULT_CONFIG_PATH
from .autocomplete import complete_argument, profile_completer


class Sshoot:
    """Manage multiple sshuttle VPN sessions."""

    # Map names to profile fileds
    _fields_map = (
        ('Remote host', 'remote'),
        ('Subnets', 'subnets'),
        ('Auto hosts', 'auto_hosts'),
        ('Auto nets', 'auto_nets'),
        ('DNS forward', 'dns'),
        ('Exclude subnets', 'exclude_subnets'),
        ('Seed hosts', 'seed_hosts'),
        ('Extra options', 'extra_opts'))

    def __call__(self):
        args = self._get_parser().parse_args()

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
        fields = tuple(self._fields_map)
        if not args.verbose:
            # Only most basic info
            fields = fields[:2]
        columns = [name for name, _ in fields]
        columns = ['', 'Profile'] + columns

        table = PrettyTable(columns)
        table.align = 'l'
        table.vertical_char = ' '
        table.junction_char = table.horizontal_char
        table.padding_width = 0
        table.left_padding_width = 0
        table.right_padding_width = 1
        table.hrules = HEADER

        for name, profile in manager.get_profiles().items():
            row = ['*' if manager.is_running(name) else '', name]
            for _, field in fields:
                row.append(self._format(getattr(profile, field)))
            table.add_row(row)
        print(table.get_string(sortby='Profile'))

    def action_show(self, manager, args):
        """Show details on a profile."""
        name = args.name
        profile = manager.get_profile(name)

        table = PrettyTable(
            field_names=['key', 'value'], header=False, border=False)
        table.align['key'] = table.align['value'] = 'l'
        table.add_row(('Name:', name))
        status = 'ACTIVE' if manager.is_running(name) else 'STOPPED'
        table.add_row(('Status', status))
        for name, field in self._fields_map:
            table.add_row(
                ('{}:'.format(name), self._format(getattr(profile, field))))
        print(table.get_string())

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
            help='show verbose listing')

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

    def _format(self, value):
        """Convert value to string, handling special cases."""
        if isinstance(value, (list, tuple)):
            return ' '.join(value)
        if value is None:
            return ''
        return value

    def _exit(self, message=None, code=1):
        """Terminate with the specified error and code ."""
        if message:
            sys.stderr.write('{}\n'.format(message))
        sys.exit(code)


sshoot = Sshoot()
