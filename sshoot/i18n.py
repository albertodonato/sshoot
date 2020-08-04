"""Internationalization setup."""

import argparse
import gettext
import os
from typing import Callable


def _setup_i18n():
    """Setup internationalization."""
    argparse._ = _get_i18n_func("argparse")
    return _get_i18n_func("sshoot")  # default domain


def _get_i18n_func(domain: str):
    """Return the internationalization function."""
    localedir = os.path.join(os.path.dirname(__file__), "locale")
    g = gettext.translation(domain, localedir=localedir, fallback=True)
    return g.gettext


_: Callable[[str], str] = _setup_i18n()
