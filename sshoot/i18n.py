"""Internationalization setup."""

import argparse
import gettext
from pathlib import Path
from typing import Callable


def _setup_i18n():
    """Setup internationalization."""
    argparse._ = _get_i18n_func("argparse")
    return _get_i18n_func("sshoot")  # default domain


def _get_i18n_func(domain: str):
    """Return the internationalization function."""
    localedir = Path(__file__).parent / "locale"
    g = gettext.translation(domain, localedir=localedir, fallback=True)
    return g.gettext


_: Callable[[str], str] = _setup_i18n()
