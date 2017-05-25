"""A sshuttle VPN profile."""


class ProfileError(Exception):
    """Profile configuration is not correct."""

    def __init__(self):
        super().__init__('Subnets must be specified')


class Profile(object):
    """Hold information about a sshuttle profile."""

    _config_attrs = (
        'remote', 'subnets', 'auto_hosts', 'auto_nets', 'dns',
        'exclude_subnets', 'seed_hosts', 'extra_opts')

    remote = None
    subnets = None
    auto_hosts = False
    auto_nets = False
    dns = False
    exclude_subnets = None
    seed_hosts = None
    extra_opts = None

    def __init__(self, subnets):
        self.subnets = subnets

    @classmethod
    def from_dict(cls, config):
        """Create a profile from a dict holding config attributes."""
        config = config.copy()  # shallow, only first-level keys are changed
        try:
            subnets = config.pop('subnets')
        except KeyError:
            raise ProfileError()

        profile = Profile(subnets=subnets)
        for attr in cls._config_attrs:
            value = config.get(attr)
            if value is not None:
                setattr(profile, attr, value)
        return profile

    def cmdline(self, executable='sshuttle', extra_opts=None):
        """Return a sshuttle cmdline based on the profile."""
        cmd = [executable] + self.subnets
        if self.remote:
            cmd.append('--remote={}'.format(self.remote))
        if self.auto_hosts:
            cmd.append('--auto-hosts')
        if self.auto_nets:
            cmd.append('--auto-nets')
        if self.dns:
            cmd.append('--dns')
        if self.exclude_subnets:
            cmd.extend(
                '--exclude={}'.format(net) for net in self.exclude_subnets)
        if self.seed_hosts:
            cmd.append('--seed-hosts={}'.format(','.join(self.seed_hosts)))
        if self.extra_opts:
            cmd.extend(self.extra_opts)
        if extra_opts:
            cmd.extend(extra_opts)
        return cmd

    def config(self):
        """Return profile configuration as a dict."""
        conf = {}
        for attr in self._config_attrs:
            value = getattr(self, attr)
            if value:
                conf[attr] = value
        return dict(conf)

    def __eq__(self, other):
        return all(
            getattr(self, attr) == getattr(other, attr)
            for attr in self._config_attrs)
