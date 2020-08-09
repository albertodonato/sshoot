"""A sshuttle VPN profile."""

import dataclasses
from typing import (
    Any,
    Dict,
    List,
    Optional,
)


class ProfileError(Exception):
    """Profile configuration is not correct."""

    def __init__(self):
        super().__init__("Subnets must be specified")


@dataclasses.dataclass
class Profile:
    """Hold information about a sshuttle profile."""

    subnets: List[str]
    remote: str = ""
    auto_hosts: bool = False
    auto_nets: bool = False
    dns: bool = False
    exclude_subnets: Optional[List[str]] = None
    seed_hosts: Optional[List[str]] = None
    extra_opts: Optional[List[str]] = None

    @classmethod
    def from_dict(cls, config: Dict[str, Any]):
        """Create a profile from a dict holding config attributes."""
        config = config.copy()  # shallow, only first-level keys are changed
        try:
            subnets = config.pop("subnets")
        except KeyError:
            raise ProfileError()

        profile = Profile(subnets=subnets)
        for attr in cls._field_names():
            value = config.get(attr)
            if value is not None:
                setattr(profile, attr, value)
        return profile

    def cmdline(
        self, executable: str = "sshuttle", extra_opts: Optional[List[str]] = None
    ) -> List[str]:
        """Return a sshuttle cmdline based on the profile."""
        cmd = [executable] + self.subnets
        if self.remote:
            cmd.append("--remote={}".format(self.remote))
        if self.auto_hosts:
            cmd.append("--auto-hosts")
        if self.auto_nets:
            cmd.append("--auto-nets")
        if self.dns:
            cmd.append("--dns")
        if self.exclude_subnets:
            cmd.extend("--exclude={}".format(net) for net in self.exclude_subnets)
        if self.seed_hosts:
            cmd.append("--seed-hosts={}".format(",".join(self.seed_hosts)))
        if self.extra_opts:
            cmd.extend(self.extra_opts)
        if extra_opts:
            cmd.extend(extra_opts)
        return cmd

    def config(self) -> Dict[str, Any]:
        """Return profile configuration as a dict."""
        conf = {}
        for attr in self._field_names():
            value = getattr(self, attr)
            if value:
                conf[attr] = value
        return dict(conf)

    @classmethod
    def _field_names(cls) -> List[str]:
        return [field.name for field in dataclasses.fields(cls)]
