"""Shell completion helpers."""

from .manager import Manager


def complete_argument(argument, completer):
    """wrapper for setting up argument completer."""
    argument.completer = completer
    return argument


def profile_completer(prefix, parsed_args, running=None, **kwargs):
    """Autocomplete helper for profile names.

    Parameters:
        - running: filter profiles that are running or not (by default no
          filter is applied).

    """
    manager = Manager(config_path=parsed_args.config)
    manager.load_config()
    for name in manager.get_profiles().keys():
        if not name.startswith(prefix):
            continue
        if running is None or manager.is_running(name) == running:
            # Either no filter is set or it matches the profile status
            yield name
