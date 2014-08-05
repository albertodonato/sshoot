#
# This file is part of sshoot.

# sshoot is free software: you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.

# sshoot is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with sshoot.  If not, see <http://www.gnu.org/licenses/>.

"""
Base class for scripts.
"""

import sys


class ErrorExitMessage(Exception):
    """
    Exception raised to exit the process with the specified message and exit
    code.
    """

    def __init__(self, message, code=1):
        super(ErrorExitMessage, self).__init__(message)
        self.code = code


class Script(object):

    exit = sys.exit

    def __init__(self, stdout=sys.stdout, stderr=sys.stderr):
        self._stdout = stdout
        self._stderr = stderr

    def get_parser(self):
        """Return a configured L{argparse.ArgumentParser} instance."""
        raise NotImplementedError()

    def main(self, args):
        """Body of the script.

        @args: the L{argparse.Namespace} instance returned by C{get_parser}.

        """
        raise NotImplementedError()

    def __call__(self, args=None):
        parser = self.get_parser()
        parsed_args = parser.parse_args(args=args)
        try:
            self.main(parsed_args)
        except ErrorExitMessage as error:
            self._error_exit(error)

    def _error_exit(self, error):
        """Terminate with the specified L{ErrorExitMessage}."""
        self._stderr.write(error.message + "\n")
        self.exit(error.code)
