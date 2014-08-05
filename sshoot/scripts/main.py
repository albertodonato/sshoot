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
from sshoot.config import Config, CONFIG_FILE


class Sshoot(Script):
    """Handle sshuttle VPN sessions."""

    def get_parser(self):
        parser = ArgumentParser(
            description="Handle multiple sshuttle sessions")
        parser.add_argument(
            "-c", "--config", default=CONFIG_FILE,
            help="configuration file to use [default %(default)s)]")
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
            "-r", "--remote", help="remote host to connect to")
        create_parser.add_argument(
            "-s", "--subnets", nargs="+",
            help="subnets to route over the VPN")
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
            "-S", "--seed-host", nargs="+",
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
            config = self._get_config(filename=args.config)
        except IOError as e:
            raise ErrorExitMessage(str(e))
        method = getattr(self, "_action_" + args.action)
        return method(config, args)

    def _get_config(self, filename=None):
        """Return the config from the specified filename."""
        config = Config()
        config.load(filename=filename)
        return config

    def _action_create(self, config, args):
        """Create a new profile."""
        name = args.name
        if name in config.profiles():
            raise ErrorExitMessage(
                "Profile name already in use: {}".format(name))

        try:
            profile = Profile.from_dict(args.__dict__)
            config.add_profile(name, profile)
        except ProfileError as e:
            raise ErrorExitMessage(str(e))

        config.save(filename=args.config)
        print("Profile created: {}".format(name))

    def _action_delete(self, config, args):
        """Delete profile with the given name."""
        name = args.name
        try:
            config.remove_profile(name)
        except KeyError:
            raise ErrorExitMessage("Unknown profile: {}".format(name))
        config.save(filename=args.config)
        print("Profile deleted: {}".format(name))

    def _action_list(self, config, args):
        """Print out the list of profiles as a table."""
        columns = ["Profile", "Active", "Remote host", "Subnets"]
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

        for name, profile in config.profiles().iteritems():
            row = [
                name,
                " ",  # XXX implement
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

    def _format(self, value):
        if isinstance(value, (list, tuple)):
            return " ".join(value)
        if value is None:
            return ""
        return value


sshoot = Sshoot()
