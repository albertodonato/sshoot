"""Command-line interface to handle sshuttle VPN sessions."""

from argparse import (
    ArgumentParser,
    Namespace,
)
from functools import partial
from typing import Set

from argcomplete import autocomplete
from toolrack.script import (
    ErrorExitMessage,
    Script,
)

from . import __version__
from .autocomplete import (
    complete_argument,
    profile_completer,
)
from .i18n import _
from .listing import (
    profile_details,
    ProfileListing,
)
from .manager import (
    DEFAULT_CONFIG_PATH,
    Manager,
    ManagerProfileError,
)


class Sshoot(Script):
    """Manage multiple sshuttle VPN sessions."""

    def main(self, args: Namespace):
        try:
            manager = Manager(config_path=args.config)
            manager.load_config()
        except IOError as error:
            raise ErrorExitMessage(error, code=3)
        action = args.action.replace("-", "_")
        method = getattr(self, "action_" + action)
        action_args = Namespace(
            **{
                key: value
                for key, value in args.__dict__.items()
                if key not in self.global_args
            }
        )
        try:
            return method(manager, action_args)
        except ManagerProfileError as error:
            raise ErrorExitMessage(error, code=2)

    def print(self, *args, **kwargs):
        """Print out message."""
        print(*args, **kwargs, file=self._stdout)

    def action_list(self, manager: Manager, args: Namespace):
        """Print out the list of profiles as a table."""
        listing = ProfileListing(manager)
        self.print(listing.get_output(args.format, verbose=args.verbose), end="")

    def action_show(self, manager: Manager, args: Namespace):
        """Show details on a profile."""
        self.print(profile_details(manager, args.name))

    def action_create(self, manager: Manager, args: Namespace):
        """Create a new profile."""
        details = args.__dict__.copy()
        details.pop("name")
        manager.create_profile(args.name, details)

    def action_delete(self, manager: Manager, args: Namespace):
        """Delete profile with the given name."""
        manager.remove_profile(args.name)

    def action_start(self, manager: Manager, args: Namespace):
        """Start sshuttle for the specified profile."""
        manager.start_profile(args.name, extra_args=args.args)
        self.print(_("Profile started"))

    def action_stop(self, manager: Manager, args: Namespace):
        """Stop sshuttle for the specified profile."""
        manager.stop_profile(args.name)
        self.print(_("Profile stopped"))

    def action_restart(self, manager: Manager, args: Namespace):
        """Restart sshuttle for the specified profile."""
        manager.restart_profile(args.name, extra_args=args.args)
        self.print(_("Profile restarted"))

    def action_is_running(self, manager: Manager, args: Namespace):
        """Return whether the specified profile is running."""
        # raise an error if profile is unknown
        manager.get_profile(args.name)
        retval = 0 if manager.is_running(args.name) else 1
        self.exit(retval)

    def action_get_command(self, manager: Manager, args: Namespace):
        """Print the sshuttle command for the specified profile."""
        cmdline = manager.get_cmdline(args.name)
        self.print(" ".join(cmdline))

    def get_parser(self) -> ArgumentParser:
        """Return a configured argparse.ArgumentParse instance."""
        parser = ArgumentParser(description=_("Manage multiple sshuttle VPN sessions"))
        parser.add_argument(
            "-V",
            "--version",
            action="version",
            version="%(prog)s {}".format(__version__),
        )
        parser.add_argument(
            "-C",
            "--config",
            default=DEFAULT_CONFIG_PATH,
            help=_("configuration directory (default: %(default)s)"),
        )
        subparsers = parser.add_subparsers(
            metavar="ACTION", dest="action", help=_("action to perform")
        )
        subparsers.required = True

        # List profiles
        list_parser = subparsers.add_parser("list", help=_("list defined profiles"))
        list_parser.add_argument(
            "-v", "--verbose", action="store_true", help=_("verbose listing")
        )
        list_parser.add_argument(
            "-f",
            "--format",
            choices=ProfileListing.supported_formats(),
            default="table",
            help=_("listing format (default %(default)s)"),
        )

        # Show profile
        show_parser = subparsers.add_parser(
            "show", help=_("show profile configuration")
        )
        complete_argument(
            show_parser.add_argument("name", help=_("profile name")), profile_completer
        )

        # Add profile
        create_parser = subparsers.add_parser("create", help=_("define a new profile"))
        create_parser.add_argument("name", help=_("profile name"))
        create_parser.add_argument(
            "subnets", nargs="+", help=_("subnets to route over the VPN")
        )
        create_parser.add_argument(
            "-r", "--remote", help=_("remote host to connect to")
        )
        create_parser.add_argument(
            "-H",
            "--auto-hosts",
            action="store_true",
            help=_("automatically update /etc/hosts with hosts from VPN"),
        )
        create_parser.add_argument(
            "-N",
            "--auto-nets",
            action="store_true",
            help=_("automatically route additional nets from server"),
        )
        create_parser.add_argument(
            "-d",
            "--dns",
            action="store_true",
            help=_("forward DNS queries through the VPN"),
        )
        create_parser.add_argument(
            "-x",
            "--exclude-subnets",
            nargs="+",
            help=_("exclude subnets from VPN forward"),
        )
        create_parser.add_argument(
            "-S",
            "--seed-hosts",
            nargs="+",
            help=_("comma-separated list of hosts to seed to auto-hosts"),
        )
        create_parser.add_argument(
            "--extra-opts",
            type=str.split,
            help=_("extra arguments to pass to sshuttle command line"),
        )

        # Remove profile
        delete_parser = subparsers.add_parser(
            "delete", help=_("delete an existing profile")
        )
        complete_argument(
            delete_parser.add_argument("name", help=_("name of the profile to remove")),
            profile_completer,
        )

        # Start profile
        start_parser = subparsers.add_parser(
            "start", help=_("start a VPN session for a profile")
        )
        complete_argument(
            start_parser.add_argument("name", help=_("name of the profile to start")),
            partial(profile_completer, running=False),
        )
        start_parser.add_argument(
            "args",
            nargs="*",
            help=_("additional arguments passed to sshuttle command line"),
        )

        # Stop profile
        stop_parser = subparsers.add_parser(
            "stop", help=_("stop a running VPN session for a profile")
        )
        complete_argument(
            stop_parser.add_argument("name", help=_("name of the profile to stop")),
            partial(profile_completer, running=True),
        )

        # Restart profile
        restart_parser = subparsers.add_parser(
            "restart", help=_("restart a VPN session for a profile")
        )
        complete_argument(
            restart_parser.add_argument(
                "name", help=_("name of the profile to restart")
            ),
            partial(profile_completer, running=True),
        )
        restart_parser.add_argument(
            "args",
            nargs="*",
            help=_("additional arguments passed to sshuttle command line"),
        )

        # Return whether profile is running
        is_running_parser = subparsers.add_parser(
            "is-running", help=_("return whether a profile is running")
        )
        complete_argument(
            is_running_parser.add_argument(
                "name", help=_("name of the profile to query")
            ),
            profile_completer,
        )

        # Get profile command
        get_command_parser = subparsers.add_parser(
            "get-command", help=_("return the sshuttle command for a profile")
        )
        complete_argument(
            get_command_parser.add_argument("name", help=_("name of the profile")),
            profile_completer,
        )

        # track global arguments/options so they can be stripped from action namespace
        self.global_args: Set[str] = set()
        for group in parser._action_groups:
            self.global_args.update(action.dest for action in group._group_actions)

        # Setup autocompletion
        autocomplete(parser)
        return parser


sshoot = Sshoot()
