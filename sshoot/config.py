"""Handle configuration files."""

from pathlib import Path
from typing import (
    Any,
    Dict,
    IO,
    Optional,
)

import yaml

from .profile import Profile


def yaml_dump(data: Dict, fh: Optional[IO] = None):
    """Dump data in YAML format with sane defaults for readability."""
    return yaml.safe_dump(data, fh, default_flow_style=False, allow_unicode=True)


class Config:
    """Handle configuration file loading/saving."""

    CONFIG_KEYS = frozenset(["executable"])

    def __init__(self, path: Path):
        self._config_file = path / "config.yaml"
        self._profiles_file = path / "profiles.yaml"
        self._reset()

    def load(self):
        """Load configuration from file."""
        self._reset()
        self._config = self._load_yaml_file(self._config_file)
        profiles = self._load_yaml_file(self._profiles_file)
        for name, conf in profiles.items():
            self._profiles[name] = Profile.from_config(conf)

    def save(self):
        """Save profiles configuration to file."""
        config = {name: profile.config() for name, profile in self._profiles.items()}
        self._profiles_file.write_text(yaml_dump(config))

    def add_profile(self, name: str, profile: Profile):
        """Add a profile to the configuration."""
        if name in self._profiles:
            raise KeyError(name)
        self._profiles[name] = profile

    def remove_profile(self, name: str):
        """Add the given profile to the configuration."""
        del self._profiles[name]

    @property
    def profiles(self) -> Dict[str, Profile]:
        """Return a dict with profiles, using names as key."""
        return self._profiles.copy()

    @property
    def config(self) -> Dict[str, Any]:
        """Return a dict with the configuration."""
        return {
            key: value for key, value in self._config.items() if key in self.CONFIG_KEYS
        }

    def _reset(self):
        """Reset default empty config."""
        self._profiles: Dict[str, Profile] = {}
        self._config = {}

    def _load_yaml_file(self, path: Path) -> Dict[str, Any]:
        """Load the specified YAML file."""
        if not path.exists():
            return {}

        return yaml.safe_load(path.read_text()) or {}
