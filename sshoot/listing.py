"""Helpers for listing output."""

from collections import OrderedDict
from csv import DictWriter
from io import StringIO
import json
from typing import (
    cast,
    Iterable,
    List,
    Optional,
    Protocol,
    Tuple,
)

from prettytable import (
    HEADER,
    PrettyTable,
)

from .config import yaml_dump
from .i18n import _
from .manager import Manager
from .profile import Profile

# Map names to profile fields
_FIELDS_MAP = OrderedDict(
    [
        (_("Remote host"), "remote"),
        (_("Subnets"), "subnets"),
        (_("Auto hosts"), "auto_hosts"),
        (_("Auto nets"), "auto_nets"),
        (_("DNS forward"), "dns"),
        (_("Exclude subnets"), "exclude_subnets"),
        (_("Seed hosts"), "seed_hosts"),
        (_("Extra options"), "extra_opts"),
    ]
)

NAME_FIELD = _("Name")
STATUS_FIELD = _("Status")


class InvalidFormat(Exception):
    def __init__(self, name: str):
        super().__init__(_("Invalid output format: {name}").format(name=name))


ProfileIterator = Iterable[Tuple[str, Profile]]


class Formatter(Protocol):
    def __call__(
        self, profile_iter: ProfileIterator, verbose: bool = False
    ) -> str:
        ...  # pragma: nocoverage


class ProfileListing:
    """List details for details in the specified format."""

    def __init__(self, manager: Manager):
        self.manager = manager

    @classmethod
    def supported_formats(cls) -> List[str]:
        return sorted(
            attr[8:] for attr in dir(cls) if attr.startswith("_format_")
        )

    def get_output(self, _format: str, verbose: bool = False) -> str:
        """Return a string with listing in the specified format."""
        formatter: Optional[Formatter] = getattr(
            self, f"_format_{_format}", None
        )
        if formatter is None:
            raise InvalidFormat(_format)
        profiles_iter = self.manager.get_profiles().items()
        return formatter(profiles_iter, verbose=verbose)

    def _format_table(
        self, profiles_iter: ProfileIterator, verbose: bool = False
    ) -> str:
        """Format profiles data as a table."""
        titles = ["", NAME_FIELD]
        titles.extend(_FIELDS_MAP)
        columns = list(_FIELDS_MAP.values())
        if not verbose:
            # Only basic info
            titles = titles[:4]
            columns = columns[:2]

        table = PrettyTable(titles)
        table.align = "l"
        table.vertical_char = " "
        table.junction_char = table.horizontal_char
        table.padding_width = 0
        table.left_padding_width = 0
        table.right_padding_width = 1
        table.hrules = HEADER

        for name, profile in profiles_iter:
            row = ["*" if self.manager.is_running(name) else "", name]
            row.extend(
                _format_value(getattr(profile, column)) for column in columns
            )
            table.add_row(row)
        return cast(str, table.get_string(sortby=NAME_FIELD)) + "\n"

    def _format_csv(
        self, profiles_iter: ProfileIterator, verbose: bool = False
    ) -> str:
        """Format profiles data as CSV."""
        titles = [NAME_FIELD, STATUS_FIELD]
        titles.extend(_FIELDS_MAP)

        buf = StringIO()
        writer = DictWriter(buf, fieldnames=titles)
        writer.writeheader()

        for name, profile in profiles_iter:
            row = {
                NAME_FIELD: name,
                STATUS_FIELD: _profile_status(self.manager, name),
            }
            row.update(
                {
                    title: getattr(profile, _FIELDS_MAP[title])
                    for title in titles[2:]
                }
            )
            writer.writerow(row)
        return buf.getvalue()

    def _format_json(
        self, profiles_iter: ProfileIterator, verbose: bool = False
    ) -> str:
        """Format profiles data as JSON."""
        data = {}
        for name, profile in profiles_iter:
            config = profile.config()
            # config['active'] = manager.is_running(name)
            data[name] = config

        return json.dumps(data)

    def _format_yaml(
        self, profiles_iter: ProfileIterator, verbose: bool = False
    ) -> str:
        """Format profiles data as YAML."""
        data = {name: profile.config() for name, profile in profiles_iter}
        return cast(str, yaml_dump(data))


def profile_details(manager: Manager, name: str) -> str:
    """Return a string with details about a profile, formatted as a table."""
    profile = manager.get_profile(name)
    table = PrettyTable(
        field_names=["key", "value"], header=False, border=False
    )
    table.align["key"] = table.align["value"] = "l"
    table.add_row((f"{NAME_FIELD}:", name))
    table.add_row((f"{STATUS_FIELD}:", _profile_status(manager, name)))
    for name, field in _FIELDS_MAP.items():
        table.add_row((f"{name}:", _format_value(getattr(profile, field))))
    return cast(str, table.get_string())


def _profile_status(manager: Manager, name: str) -> str:
    """Return a string with the status of a profile."""
    return _("ACTIVE") if manager.is_running(name) else _("STOPPED")


def _format_value(value) -> str:
    """Convert value to string, handling special cases."""
    if isinstance(value, (list, tuple)):
        return " ".join(value)
    if value is None:
        return ""
    return str(value)
