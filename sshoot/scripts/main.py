#
# This file is part of sshoot.

# sshoot is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.

# sshoot is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with sshoot.  If not, see <http://www.gnu.org/licenses/>.

"""Command-line interface to handle sshuttle VPN sessions."""

from argparse import ArgumentParser

from prettytable import PrettyTable, HEADER

from sshoot.script import Script, ErrorExitMessage
from sshoot.profile import Profile, ProfileError
from sshoot.manager import (
    Manager, DEFAULT_CONFIG_PATH, StartProfileError, StopProfileError)


class Sshoot(Script):
    """Manage multiple sshuttle VPN sessions."""

    def get_parser(self):
        parser = ArgumentParser(description=self.__doc__)
        parser.add_argument(
            "-C", "--config", default=DEFAULT_CONFIG_PATH,
            help="configuration directory (default: %(default)s)")
        subparsers = parser.add_subparsers(
            metavar="ACTION", dest="action", help="action to perform")
        # List profiles
        list_parser = subparsers.add_parser(
            "list", help="list defined profiles")
        list_parser.add_argument(
            "-v", "--verbose", action="store_true",
            help="show verbose listing")
        # Add profile
        create_parser = subparsers.add_parser(
            "create", help="define a new profile")
        create_parser.add_argument("name", help="profile name")
        create_parser.add_argument(
            "subnets", nargs="+", help="subnets to route over the VPN")
        create_parser.add_argument(
            "-r", "--remote", help="remote host to connect to")
        create_parser.add_argument(
            "-H", "--auto-hosts", action="store_true",
            help="automatically update /etc/hosts with hosts from VPN")
        create_parser.add_argument(
            "-N", "--auto-nets", action="store_true",
            help="automatically route additional nets from server")
        create_parser.add_argument(
            "-d", "--dns", action="store_true",
            help="forward DNS queries through the VPN")
        create_parser.add_argument(
            "-x", "--exclude-subnets", nargs="+",
            help="exclude subnets from VPN forward")
        create_parser.add_argument(
            "-S", "--seed-hosts", nargs="+",
            help="comma-separated list of hosts to seed to auto-hosts")
        create_parser.add_argument(
            "--extra-opts",
            help="extra options to pass to sshuttle command line")
        # Remove profile
        delete_parser = subparsers.add_parser(
            "delete", help="delete an existing profile")
        delete_parser.add_argument(
            "name", help="name of the profile to remove")
        # Start profile
        start_parser = subparsers.add_parser(
            "start", help="start a VPN session for a profile")
        start_parser.add_argument(
            "name", help="name of the profile to start")
        # Stop profile
        stop_parser = subparsers.add_parser(
            "stop", help="stop a running VPN session for a profile")
        stop_parser.add_argument(
            "name", help="name of the profile to stop")
        return parser

    def main(self, args):
        try:
            manager = Manager(config_path=args.config)
            manager.load_config()
        except IOError as e:
            raise ErrorExitMessage(str(e))
        method = getattr(self, "_action_" + args.action)
        return method(manager, args)

    def _action_list(self, manager, args):
        """Print out the list of profiles as a table."""
        config = manager.config
        columns = ["", "Profile", "Remote host", "Subnets"]
        if args.verbose:
            columns.extend(
                ("Auto hosts", "Auto nets", "DNS forward", "Exclude subnets",
                 "Seed hosts", "Extra options"))
        table = PrettyTable(columns)
        table.align = "l"
        table.vertical_char = " "
        table.junction_char = table.horizontal_char
        table.padding_width = 0
        table.left_padding_width = 0
        table.right_padding_width = 1
        table.hrules = HEADER

        for name, profile in config.profiles.iteritems():
            row = [
                "*" if manager.is_running(name) else "",
                name,
                self._format(profile.remote),
                self._format(profile.subnets)]
            if args.verbose:
                row.extend(
                    (self._format(profile.auto_hosts),
                     self._format(profile.auto_nets),
                     self._format(profile.dns),
                     self._format(profile.exclude_subnets),
                     self._format(profile.seed_hosts),
                     self._format(profile.extra_opts)))
            table.add_row(row)
        print(table.get_string(sortby="Profile"))

    def _action_create(self, manager, args):
        """Create a new profile."""
        config = manager.config
        name = args.name

        try:
            profile = Profile.from_dict(args.__dict__)
            config.add_profile(name, profile)
        except KeyError:
            raise ErrorExitMessage(
                "Profile name already in use: {}".format(name))
        except ProfileError as e:
            raise ErrorExitMessage(str(e))

        config.save()

    def _action_delete(self, manager, args):
        """Delete profile with the given name."""
        config = manager.config
        name = args.name

        try:
            config.remove_profile(name)
        except KeyError:
            raise ErrorExitMessage("Unknown profile: {}".format(name))
        config.save()

    def _action_start(self, manager, args):
        """Start sshuttle for the specified profile."""
        try:
            manager.start_profile(args.name)
        except StartProfileError as e:
            raise ErrorExitMessage(str(e))

        print("Profile started.")

    def _action_stop(self, manager, args):
        """Stop sshuttle for the specified profile."""
        try:
            manager.stop_profile(args.name)
        except StopProfileError as e:
            raise ErrorExitMessage(str(e))

        print("Profile stopped.")

    def _format(self, value):
        if isinstance(value, (list, tuple)):
            return " ".join(value)
        if value is None:
            return ""
        return value


sshoot = Sshoot()
