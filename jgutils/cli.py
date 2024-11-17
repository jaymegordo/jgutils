import datetime
import subprocess
import sys
from argparse import ArgumentParser
from argparse import ArgumentTypeError
from datetime import datetime as dt

from dateutil import parser

from jgutils.logger import Loggable


class CustomArgumentParser(ArgumentParser, Loggable):
    """Custom argument parser with additional methods."""

    CUSTOM = dict(
        n_jobs=dict(
            type=int,
            default=50,
            help='Number of threads to use for parallel processing',
            required=False),
        limit=dict(
            type=int,
            default=None,
            help='Limit number of items'),
    )

    def __init__(self, **kw):
        super().__init__(**kw)
        Loggable.__init__(self, show_log=kw.get('show_log', True))

    def add_custom(self, name: str, *args, **kw) -> None:
        """Convenience method to add custom argument.

        Parameters
        ----------
        name : str
            Name of custom argument to add.
        """

        if not name in self.CUSTOM:
            raise ValueError(f'Custom argument "{name}" not defined')

        data = self.CUSTOM[name]
        data.update(kw)

        # Set name_or_flags if not defined
        name_or_flags = data.pop('name_or_flags', f'--{name}')  # type: str

        self.add_argument(name_or_flags, *args, **data)

    def add_multi(self, names: list[str]) -> None:
        """Convenience method to add multiple custom arguments."""
        for name in names:
            self.add_custom(name)

    def add_date(self, *args, **kw):
        """Convenience method to add date argument."""
        kw['type'] = self.validate_date
        self.add_argument(*args, **kw)

    @staticmethod
    def validate_date(s: str | None) -> dt | None:
        """Parse and return date as UTC datetime object.

        Parameters
        ----------
        s : str | None
            Date string to parse.

        Returns
        -------
        dt | None
            Parsed date as UTC datetime object if given else None.

        """
        if s is None:
            return None

        try:
            return parser.parse(s).replace(tzinfo=datetime.UTC)

        except ValueError as e:
            msg = f'Invalid date: "{s}". Please use a format parseable by datetime.parser'
            raise ArgumentTypeError(msg) from e

    def run_cmd(self, cmd: list[str] | str, shell: bool = True) -> subprocess.CompletedProcess:
        """Run command and log output.

        Parameters
        ----------
        cmd : list[str] | str
            Command to run.
        shell : bool, optional
            Whether to run command in shell, by default False
            If shell is True, cmd will be coerced to string

        Returns
        -------
        subprocess.CompletedProcess
        """
        cmd_str = ' '.join(cmd) if isinstance(cmd, list) else cmd
        shell = isinstance(cmd, str) or shell

        if shell and not isinstance(cmd, str):
            cmd = ' '.join(cmd)

        self.info(cmd_str)

        try:
            return subprocess.run(cmd, check=True, shell=shell)
        except subprocess.CalledProcessError as e:
            # execution stops on first error
            self.err(str(e))
            sys.exit(1)

    def run_cmds(
            self,
            cmds: list[list[str]] | list[str],
            shell: bool = True) -> list[subprocess.CompletedProcess]:
        """Run multiple commands and log output.

        Parameters
        ----------
        cmds : list[list[str]] | list[str]
            List of commands to run.
        shell : bool, optional
            Whether to run command in shell, by default False

        Returns
        -------
        list[subprocess.CompletedProcess]
        """
        return [self.run_cmd(cmd, shell=shell) for cmd in cmds]
