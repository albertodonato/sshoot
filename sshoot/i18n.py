"""Internationalization setup."""

import os
import gettext


def _get_i18n_func():
    """Return the internationalization function."""
    locale_path = os.path.join(os.path.dirname(__file__), 'locale')
    translation = gettext.translation('sshoot', locale_path, fallback=True)
    return translation.gettext


_ = _get_i18n_func()
