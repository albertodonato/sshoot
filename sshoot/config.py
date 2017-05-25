"""Handle configuration files."""

import yaml
import os

from .profile import Profile


def yaml_dump(data, fh=None):
    """Dump data in YAML format with sane defaults for readability."""
    return yaml.safe_dump(
        data, fh, default_flow_style=False, allow_unicode=True)


class Config(object):
    """Handle configuration file loading/saving."""

    CONFIG_KEYS = frozenset(['executable'])

    def __init__(self, path):
        self._config_file = os.path.join(path, 'config.yaml')
        self._profiles_file = os.path.join(path, 'profiles.yaml')
        self._reset()

    def load(self):
        """Load configuration from file."""
        self._reset()
        self._config = self._load_yaml_file(self._config_file)
        profiles = self._load_yaml_file(self._profiles_file)
        for name, conf in profiles.items():
            self._profiles[name] = Profile.from_dict(self._from_config(conf))

    def save(self):
        """Save profiles configuration to file."""
        with open(self._profiles_file, 'w') as fh:
            yaml_dump(self._build_profiles_config(), fh)

    def add_profile(self, name, profile):
        """Add a profile to the configuration."""
        if name in self._profiles:
            raise KeyError(name)
        self._profiles[name] = profile

    def remove_profile(self, name):
        """Add the given profile to the configuration."""
        del self._profiles[name]

    @property
    def profiles(self):
        """Return a dict with profiles, using names as key."""
        return self._profiles.copy()

    @property
    def config(self):
        """Return a dict with the configuration."""
        return {
            key: value for key, value in self._config.items()
            if key in self.CONFIG_KEYS}

    def _reset(self):
        """Reset default empty config."""
        self._profiles = {}
        self._config = {}

    def _load_yaml_file(self, path):
        """Load the specified YAML file."""
        if not os.path.exists(path):
            return {}

        with open(path) as fh:
            # None is returned for empty config file
            return yaml.load(fh) or {}

    def _build_profiles_config(self):
        """Return the profiles config dict to be saved to file."""
        return {
            name: self._to_config(profile.config())
            for name, profile in self._profiles.items()}

    def _from_config(self, config):
        """Convert a config to a params dict."""
        return {
            key.replace('-', '_'): value
            for key, value in config.items()}

    def _to_config(self, params):
        """Convert a params dict to a config."""
        return {
            key.replace('_', '-'): value
            for key, value in params.items()}
