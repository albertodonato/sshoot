"""Manage multiple sshuttle VPN sessions."""

import pkg_resources

__all__ = ["PACKAGE", "__version__"]

PACKAGE = pkg_resources.get_distribution("sshoot")

__version__ = PACKAGE.version
