"""Internationalization setup."""

import os
import gettext
import argparse


def _setup_i18n():
    """Setup internationalization."""
    argparse._ = _get_i18n_func('argparse')
    return _get_i18n_func('sshoot')  # default domain


def _get_i18n_func(domain):
    """Return the internationalization function."""
    localedir = os.path.join(os.path.dirname(__file__), 'locale')
    g = gettext.translation(domain, localedir=localedir, fallback=True)
    return g.gettext


gettext = _setup_i18n()
