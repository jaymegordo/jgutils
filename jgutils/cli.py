import datetime
import re
import subprocess
import sys
from argparse import ArgumentParser
from argparse import ArgumentTypeError
from typing import TYPE_CHECKING
from typing import Any

from dateutil import parser

from jgutils.env import Env
from jgutils.logger import Loggable

if TYPE_CHECKING:
    from jgutils.typing import DtNone


def str2bool(v: Any) -> bool:  # noqa: ANN401
    """Convert string to boolean

    Parameters
    ----------
    v : Any
        Value to convert to boolean

    Returns
    -------
    bool
    """
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise ArgumentTypeError(f'Boolean value expected. Got "{v}"')


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
        env=dict(
            type=Env,
            default=Env.LOCAL,
            choices=Env.values(),
            help='Environment to run in'),
        profile=dict(
            type=str,
            default=None,
            help='AWS profile to use'),
        raise_errors=dict(
            type=str2bool,
            default=False,
            help='Raise errors in threads or ignore'),
    )

    def __init__(self, description: str | None = None, **kw):
        super().__init__(description=description, **kw)
        Loggable.__init__(self, show_log=kw.get('show_log', True))

    def show_args(self) -> None:
        """Show all arguments."""
        from jgutils.pretty import PD  # noqa: PLC0415 - lazy load for display purposes

        # Get all arguments as a dictionary
        data = {
            key: value for key, value in vars(self.parse_args()).items()
            if not key.startswith('_')
        }
        PD(data).display()

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

        self.add_argument(name_or_flags, *args, **data)  # type: ignore[arg-type]

    def add_multi(self, names: list[str]) -> None:
        """Convenience method to add multiple custom arguments."""
        for name in names:
            self.add_custom(name)

    def add_date(self, *args, **kw):
        """Convenience method to add date argument."""
        kw['type'] = self.validate_date
        self.add_argument(*args, **kw)

    @staticmethod
    def validate_date(s: str | None) -> 'DtNone':
        """Parse and return date as UTC datetime object.

        Parameters
        ----------
        s : str | None
            Date string to parse.

        Returns
        -------
        DtNone
            Parsed date as UTC datetime object if given else None.

        """
        if s is None:
            return None

        try:
            return parser.parse(s).replace(tzinfo=datetime.UTC)

        except ValueError as e:
            msg = f'Invalid date: "{s}". Please use a format parseable by datetime.parser'
            raise ArgumentTypeError(msg) from e

    def run_cmd(
            self,
            cmd: list[str | None] | str,
            shell: bool = True,
            allowed_error: str | None = None,
            check: bool = True,
            **kw) -> subprocess.CompletedProcess:
        """Run command and log output.

        Parameters
        ----------
        cmd : list[str | None] | str
            Command to run. None values in lists are automatically filtered out.
        shell : bool, optional
            Whether to run command in shell, by default True
            If shell is True, cmd will be coerced to string
        allowed_error : str | None, optional
            Error message to suppress, by default None
        check : bool, optional
            Whether to raise CalledProcessError on non-zero exit, by default True

        Returns
        -------
        subprocess.CompletedProcess
            Always returns CompletedProcess. On unhandled errors, calls sys.exit(1).

        Raises
        ------
        ValueError
            If cmd is empty after filtering None values.
        """
        # filter out Nones from lists and narrow type
        cmd_clean: list[str] | str
        if isinstance(cmd, list):
            cmd_clean = [c for c in cmd if c is not None]
            if not cmd_clean:
                raise ValueError('Command is empty after filtering None values')
        else:
            cmd_clean = cmd

        cmd_str = ' '.join(cmd_clean) if isinstance(cmd_clean, list) else cmd_clean
        shell = isinstance(cmd_clean, str) or shell

        # Convert list to string if shell mode
        cmd_final: str | list[str]
        if shell and isinstance(cmd_clean, list):
            cmd_final = ' '.join(cmd_clean)
        else:
            cmd_final = cmd_clean

        self.info(cmd_str)

        # Copy and sanitize **kw to avoid multiple stderr= values
        if 'stderr' not in kw:
            kw['stderr'] = subprocess.PIPE if allowed_error else None

        try:
            return subprocess.run(
                cmd_final,
                check=check,
                shell=shell,
                **kw)

        except subprocess.CalledProcessError as e:

            # Suppress error if allowed_error is found in stderr
            stderr_decoded = e.stderr.decode() if e.stderr else ''
            if allowed_error and re.search(allowed_error, stderr_decoded, flags=re.IGNORECASE):
                self.warning(f'Suppressed allowed error: {allowed_error}')
                # Return a successful result when error is suppressed
                return subprocess.CompletedProcess(
                    args=e.cmd,
                    returncode=0,
                    stdout=e.stdout,
                    stderr=e.stderr)
            else:
                self.err(str(e))
                sys.exit(1)

    def run_cmds(
            self,
            cmds: list[list[str | None] | str | None],
            shell: bool = True,
            allowed_error: str | None = None,
            **kw) -> list[subprocess.CompletedProcess]:
        """Run multiple commands and log output.

        Parameters
        ----------
        cmds : list[list[str | None] | str | None]
            List of commands to run. None values and empty commands are filtered out.
        shell : bool, optional
            Whether to run command in shell, by default True
        allowed_error : str | None, optional
            Error message to suppress, by default None

        Returns
        -------
        list[subprocess.CompletedProcess]
            List of completed processes (empty commands are filtered out).
        """
        return [
            self.run_cmd(cmd, shell=shell, allowed_error=allowed_error, **kw)
            for cmd in cmds
            if cmd]
