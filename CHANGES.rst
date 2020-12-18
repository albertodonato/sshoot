v1.5.1 - 2020-12-18
===================

- [snap] Ship Python3.8 in the snap not to depend on version from OS.
- Drop legacy config file path compatiblity.
- Drop Python3.6 support.
* Add unittests for main script.
* Only pass action parameters to Manager methods (Fixes: #10).


v1.5.0 - 2020-11-20
===================

- Add ``restart`` option for a profile.
- Use ``toolrack.script.Script`` as base for main script.
- [snap] Move to ``core20``.
- Add type hints.


v1.4.2 - 2019-06-13
===================

- Rework tests and project setup.
- Fix yaml warning (Fixes: #6).


v1.4.1 - 2018-06-30
===================

-  Use pathlib.Path instead of strings.
-  I8n-related cleanups.


v1.4.0 - 2017-10-22
===================

-  Add i18n support and it_IT translation.


v1.3.2 - 2017-10-15
===================

-  Use ``pyxdg`` instead of ``xdg``.


v1.3.1 - 2017-10-10
===================

-  Specify long description content-type.


v1.3.0 - 2017-10-02
===================

-  Support profiles listing in different formats (table, CSV, YAML,
   JSON) (Fixes: #3).
-  Move configuration path to XDG conventions (Fixes: #1).


v1.2.6 - 2017-05-25
===================

-  Move project to GitHub, small test cleanups.


v1.2.5 - 2016-11-29
===================

-  Filter running sessions for start/stop commands autocompletion.


v1.2.4 - 2016-11-20
===================

-  Fix autocompletion setup again.


v1.2.3 - 2016-11-20
===================

-  Fix autocompletion.


v1.2.2 - 2016-11-20
===================

-  Add support for bash-completion.


v1.2.1 - 2015-11-04
===================

-  Fix error message decoding when profile fails to start.


v1.2.0 - 2015-09-04
===================

-  Add is-running command to check whether a profile is running.


v1.1.0 - 2015-05-27
===================

-  Switch to Python3.


v1.0.3 - 2015-04-15
===================

-  Support passing extra options to sshuttle when starting a profile.


v1.0.1 - 2014-11-23
===================

-  Add get-command subcommand to return the sshuttle command line.


v1.0.0 - 2014-10-08
===================

-  Separate (optional) configuration and sessions files.
-  Directory for pidfiles is created in temporary directory, rather than
   home, to avoid issues if the home is shared.


v0.0.3 - 2014-09-01
===================

-  Fix dependencies.


v0.0.2 - 2014-08-24
===================

-  Support for managing sshuttle sessions (add, remove start, stop).


v0.0.1 - 2014-08-05
===================

-  Initial release.
