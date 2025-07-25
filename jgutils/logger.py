import io
import logging
import os
import re
import sys
import traceback
from logging.handlers import RotatingFileHandler
from typing import TYPE_CHECKING
from typing import Any

from jgutils.config import IS_REMOTE

try:
    import colored_traceback
    import colorlog
    import pygments.lexers
    from colored_traceback import Colorizer

    # color tracebacks in terminal - uncaught exceptions in scripts only, not logging
    colored_traceback.add_hook(style='jayme', always=True)
    Formatter = colorlog.ColoredFormatter
except ModuleNotFoundError:
    # running on remote
    Formatter = logging.Formatter

if TYPE_CHECKING:
    from collections.abc import Callable  # noqa: F401

    from jgutils.errors import CustomSentryIntegration

# simple colors
_palette = dict(
    black=30,
    red=31,
    green=32,
    yellow=33,
    blue=34,
    magenta=35,
    cyan=36,
    white=37,
    underline=4,
    reset=0)

# create full color codes as a dict comp
palette = {k: f'\033[{color_code}m' for k, color_code in _palette.items()}


class ColoredFormatter(Formatter):
    """Custom logging Formatter to print colored tracebacks and log level messages
    """

    def __init__(self, fmt: str, *args, **kw) -> None:
        log_colors = dict(
            DEBUG='cyan',
            INFO='green',
            WARNING='yellow',
            ERROR='red',
            CRITICAL='red,bg_white')

        # always add log_color before format
        fmt = f'%(log_color)s{fmt}'

        super().__init__(fmt, *args, log_colors=log_colors, **kw)
        self.colorizer = Colorizer(style='jayme')

    def colorize_traceback(self, type, value, tb) -> str:  # noqa: ANN001
        """
        Copied from colored_traceback Colorizer
        - just return and print to io instead of write to stderr so logging message prints first
        """

        # import pygments.lexers
        tb_text = ''.join(traceback.format_exception(type, value, tb))
        lexer = pygments.lexers.get_lexer_by_name('pytb', stripall=True)
        return pygments.highlight(
            tb_text, lexer, self.colorizer.formatter)
        # self.stream.write(tb_colored)

    def formatException(self, ei) -> str:  # noqa: ANN001, N802
        sio = io.StringIO()

        try:
            tb_colored = self.colorize_traceback(*ei)
            print(tb_colored, file=sio)
        except TypeError:
            return super().formatException(ei)

        s = sio.getvalue()
        sio.close()

        if s[-1:] == '\n':
            s = s[:-1]

        return s

    def formatMessage(self, record: logging.LogRecord) -> str:  # noqa: N802
        message = super().formatMessage(record)
        return highlight_filepath(message)

    def format(self, record: logging.LogRecord) -> str:
        """Disable caching of exception text
        - Lets StreamHandler and FileHandler have different traceback formats

        https://stackoverflow.com/questions/5875225/
        weird-logger-only-uses-the-formatter-of-the-first-handler-for-exceptions
        """
        backup = record.exc_text
        record.exc_text = None
        s = logging.Formatter.format(self, record)
        record.exc_text = backup

        return s


class CustomLogger(logging.Logger):
    """Custom logger to send error logs to slack channel
    """

    def __init__(self, name: str, *args, **kwargs) -> None:
        super().__init__(name, *args, **kwargs)

        # this prevents duplicate outputs (eg for pytest and on aws lambda)
        # TODO this leaves duplicate output on lambda logs, would be nice to fix to improve readability there
        # from config import IS_REMOTE
        # if not IS_REMOTE:
        #     self.propagate = False  # need to allow propagation for sentry to captuer log.error

    def error(self, msg: str | None = None, *args, send_sentry: bool = True, **kw) -> None:
        """Send error to slack channel then log error as normal

        Parameters
        ----------
        send_sentry : bool, optional
            send error to sentry, by default True
        """

        kw.setdefault('extra', {}).update({'send_sentry': send_sentry})

        super().error(msg, *args, **kw)

    def _get_sentry_integration(self) -> 'CustomSentryIntegration | None':
        import sentry_sdk

        from jgutils.errors import SENTRY_INTEGRATION
        return sentry_sdk.Hub.current.get_integration(SENTRY_INTEGRATION)

    def _set_sentry(self, data_type: str, data: str | dict, value: Any = None) -> None:  # noqa: ANN401
        """Helper func to set either data or tag on sentry error

        Parameters
        ----------
        data_type : str
            either 'data' or 'tag'
        data : str | dict
            data to set
        value : Any, optional
            value to set, by default None
        """
        if not data_type in ('data', 'tag'):
            raise ValueError(
                f'data_type must be "data" or "tag", got "{data_type}"')

        if integration := self._get_sentry_integration():

            # if data is a string, convert to dict with value
            if isinstance(data, str):
                data = {data: value}

            # pass to either add_custom_data or add_custom_tag
            func = {
                'data': integration.add_custom_data,
                # type: Callable[[str, Any], None]
                'tag': integration.add_custom_tag}[data_type]

            for key, value in data.items():
                func(key, value)

    def set_sentry_data(self, data: str | dict, value: Any = None) -> None:  # noqa: ANN401
        """Function to add custom data to the Sentry error.

        Parameters
        ----------
        key : str | dict
            str as key, or dict of key/value pairs to add to sentry error
        value : Any, optional
            value to add to sentry error

        Examples
        --------
        >>> from jgutils.logger import get_log
        >>> log = get_log(__name__)
        >>> log.set_sentry_data('thing', 123)
        """
        self._set_sentry('data', data, value)

    def set_sentry_tag(self, data: str | dict, value: Any = None) -> None:  # noqa: ANN401
        """Function to add custom tag to the Sentry error.

        Parameters
        ----------
        key : str | dict
            str as key, or dict of key/value pairs to add to sentry error
        value : Any, optional
            value to add to sentry error

        Examples
        --------
        >>> from jgutils.logger import get_log
        >>> log = get_log(__name__)
        >>> log.set_sentry_tag('user', User.objects.get(id=1))
        """
        self._set_sentry('tag', data, value)


class Loggable():
    """Mixin class to generate logs if show_log is True"""

    def __init__(self, show_log: bool = True, log_level: int = logging.DEBUG) -> None:
        """
        Parameters
        ----------
        show_log : bool, optional
            show log messages, default True
        log_level : int, optional
            allow setting more precise log level to show, default logging.DEBUG
        """
        self.show_log = show_log

        # get logger
        self._log = get_log(self.__module__)
        self._log.level = log_level

    def log(
            self,
            msg: str,
            level: int = logging.INFO,
            force_show: bool = False,
            stacklevel: int = 2,
            end: str = '') -> None:
        """Logs a message of a certain level

        Parameters
        ----------
        msg : str
            message to log
        level : int, optional
            level of message, by default logging.INFO
        force_show : bool, optional
            logs the message regardless of show_log, by default False
        stacklevel : int, optional
            stack level to log from, by default 2
        end : str, optional
            string to end the log, by default ''
        """
        if self.show_log or force_show:
            self._log.log(level, f'{msg}{end}', stacklevel=stacklevel)

    def debug(self, msg: str, **kw) -> None:
        self.log(msg, logging.DEBUG, stacklevel=3, **kw)

    def info(self, msg: str, **kw) -> None:
        self.log(msg, logging.INFO, stacklevel=3, **kw)

    def warning(self, msg: str, **kw) -> None:
        self.log(msg, logging.WARNING, stacklevel=3, **kw)

    def error(self, msg: str, **kw) -> None:
        self.log(msg, logging.ERROR, stacklevel=3, **kw)

    def err(self, msg: str, **kw) -> None:
        """Convenience if base class (eg argparse) has error method already"""
        self.log(msg, logging.ERROR, stacklevel=3, **kw)

    def critical(self, msg: str, **kw) -> None:
        self.log(msg, logging.CRITICAL, stacklevel=3, **kw)

    def exception(self, msg: str, **kw) -> None:
        self.log(msg, logging.ERROR, stacklevel=3, **kw)


# TODO move this messy code into CustomLogger
if not IS_REMOTE:
    # local, use colored formatter
    StreamFormatter = ColoredFormatter
else:
    StreamFormatter = logging.Formatter

# Console/stream handler
_fmt_stream = '%(levelname)-7s %(lineno)-4d %(name)-20s %(message)s'
stream_formatter = StreamFormatter(_fmt_stream)
# In frozen apps where sys.stdout is None, use NullHandler to avoid conflicts with terminal
sh = logging.NullHandler() if sys.stdout is None else logging.StreamHandler(
    stream=sys.stdout)
sh.setFormatter(stream_formatter)

# set file logger if path set and not remote
log_path = os.getenv('file_log_path', None)  # noqa: SIM112
fh = None

if not log_path is None and not IS_REMOTE:
    _fmt_file = '%(asctime)s  %(levelname)-7s %(lineno)-4d %(name)-20s %(message)s'
    fmt_file = logging.Formatter(_fmt_file, datefmt='%m-%d %H:%M:%S')

    fh = RotatingFileHandler(log_path, maxBytes=100000, backupCount=0)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt_file)

# NOTE could do logging.basicConfig(handlers=[sh, fh]) to catch everything
# logging.basicConfig(handlers=[sh, fh], level=logging.DEBUG)
logging.setLoggerClass(CustomLogger)


def get_log(name: str) -> logging.Logger:
    """Create logger object with predefined stream handler & formatting

    Parameters
    ----------
    name : str
        module __name__

    Returns
    -------
    logging.logger

    Examples
    --------
    >>> from jgutils.logger import get_log
    >>> log = get_log(__name__)
    """
    if not IS_REMOTE:
        name = '.'.join(name.split('.')[1:])

    # cant set name to nothing or that calls the ROOT logger
    if name == '':
        name = 'base'

    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)

    if not log.handlers:
        log.addHandler(sh)

        if not fh is None:
            log.addHandler(fh)

    return log


def highlight_filepath(s: str, color: str = 'blue') -> str:
    """Highlight filepath string for output in terminal

    Parameters
    ----------
    s : str
        string to search for filepaths
    color : str, optional
        default 'blue'

    Returns
    -------
    str
        input string with filepaths colored
    """
    # try to match previous color
    # \x1b[32m
    expr = r'\x1b\[\d+m'
    match = re.search(expr, str(s))
    reset = match[0] if match else palette['reset']

    # stop at first backslash \ (color code)
    expr = r'(\S*\/.*\/[^\\]*?(?:.*\.\w{1,10}|(?=\s)|.*\/))'
    return re.sub(expr, f'{palette[color]}\\1{reset}', str(s))
