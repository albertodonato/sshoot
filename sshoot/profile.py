"""A sshuttle VPN profile."""

import dataclasses
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from .i18n import _


class ProfileError(Exception):
    """Invalid profile configuration."""


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
    def from_config(cls, config: Dict[str, Any]):
        """Create a profile from a config dict."""
        config = config.copy()
        try:
            profile = cls(config.pop("subnets"))
        except KeyError:
            raise ProfileError(_("Profile missing 'subnets' config"))
        profile.update(config)
        return profile

    def update(self, config: Dict[str, Any]):
        """Update the profile from the specified config."""
        field_names = list(self._fields())
        for key, value in config.items():
            attr = key.replace("-", "_")
            if attr not in field_names:
                raise ProfileError(
                    _("Invalid profile config '{key}'").format(key=key)
                )
            setattr(self, attr, value)

    def config(self) -> Dict[str, Any]:
        """Return profile configuration as a dict."""
        conf = {}
        for attr, default_value in self._fields().items():
            value = getattr(self, attr)
            if value != default_value:
                conf[attr.replace("_", "-")] = value
        return dict(conf)

    def cmdline(
        self,
        executable: str = "sshuttle",
        extra_opts: Optional[List[str]] = None,
        global_extra_options: Optional[List[str]] = None,
    ) -> List[str]:
        """Return a sshuttle cmdline based on the profile."""
        cmd = [executable] + self.subnets
        if self.remote:
            cmd.append(f"--remote={self.remote}")
        if self.auto_hosts:
            cmd.append("--auto-hosts")
        if self.auto_nets:
            cmd.append("--auto-nets")
        if self.dns:
            cmd.append("--dns")
        if self.exclude_subnets:
            cmd.extend(f"--exclude={net}" for net in self.exclude_subnets)
        if self.seed_hosts:
            seed_hosts = ",".join(self.seed_hosts)
            cmd.append(f"--seed-hosts={seed_hosts}")
        if self.extra_opts:
            cmd.extend(self.extra_opts)
        if extra_opts:
            cmd.extend(extra_opts)
        if global_extra_options:
            cmd.extend(global_extra_options)
        return cmd

    @classmethod
    def _fields(cls) -> Dict[str, Any]:
        return {field.name: field.default for field in dataclasses.fields(cls)}
