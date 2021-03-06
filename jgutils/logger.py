import io
import logging
import os
import re
import sys
import traceback
from logging.handlers import RotatingFileHandler

from jgutils.config import AZURE_WEB

try:
    import colored_traceback
    import colorlog
    import pygments.lexers
    from colored_traceback import Colorizer

    # color tracebacks in terminal - uncaught exceptions in scripts only, not logging
    colored_traceback.add_hook(style='jayme', always=True)
    Formatter = colorlog.ColoredFormatter
except ModuleNotFoundError:
    # running on azure
    Formatter = logging.Formatter

# simple colors
_palette = dict(
    black=30,
    red=31,
    green=32,
    yellow=33,
    blue=34,
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

        super().__init__(fmt, log_colors=log_colors, *args, **kw)
        self.colorizer = Colorizer(style='jayme')

    def colorize_traceback(self, type, value, tb) -> str:
        """
        Copied from colored_traceback Colorizer
        - just return and print to io instead of write to stderr so logging message prints first
        """

        # import pygments.lexers
        tb_text = ''.join(traceback.format_exception(type, value, tb))
        lexer = pygments.lexers.get_lexer_by_name('pytb', stripall=True)
        tb_colored = pygments.highlight(
            tb_text, lexer, self.colorizer.formatter)
        # self.stream.write(tb_colored)
        return tb_colored

    def formatException(self, ei) -> str:
        sio = io.StringIO()

        tb_colored = self.colorize_traceback(*ei)
        print(tb_colored, file=sio)

        s = sio.getvalue()
        sio.close()

        if s[-1:] == '\n':
            s = s[:-1]

        return s

    def formatMessage(self, record: logging.LogRecord) -> str:
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


if not AZURE_WEB:
    # local app, use colored formatter
    StreamFormatter = ColoredFormatter
else:
    StreamFormatter = logging.Formatter

# Console/stream handler
_fmt_stream = '%(levelname)-7s %(lineno)-4d %(name)-20s %(message)s'
stream_formatter = StreamFormatter(_fmt_stream)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setFormatter(stream_formatter)

# set file logger if path set and not azure
log_path = os.getenv('file_log_path', None)
fh = None

if not log_path is None and not AZURE_WEB:
    _fmt_file = '%(asctime)s  %(levelname)-7s %(lineno)-4d %(name)-20s %(message)s'
    fmt_file = logging.Formatter(_fmt_file, datefmt='%m-%d %H:%M:%S')

    fh = RotatingFileHandler(log_path, maxBytes=100000, backupCount=0)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt_file)

# NOTE could do logging.basicConfig(handlers=[sh, fh]) to catch everything
# logging.basicConfig(handlers=[sh, fh], level=logging.DEBUG)


def getlog(name: str) -> logging.Logger:
    """Create logger object with predefined stream handler & formatting
    - need to instantiate with logging.getLogger to inherit from azure's root logger

    Parameters
    ----------
    name : str
        module __name__

    Returns
    -------
    logging.logger

    Examples
    --------
    >>> from jambot.logger import getlog
    >>> log = getlog(__name__)
    """
    # remove __app__ prefix for azure
    name = name.replace('__app__.', '')
    name = '.'.join(name.split('.')[1:])

    # cant set name to nothing or that calls the ROOT logger
    if name == '':
        name = 'base'

    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)

    if not AZURE_WEB:
        # this prevents duplicate outputs (eg for pytest)
        log.propagate = False

    if not log.handlers:
        log.addHandler(sh)

        if not fh is None:
            log.addHandler(fh)

    return log


def highlight_filepath(s: str, color: str = 'blue') -> str:
    """Highlight filepath string for output in terminal

    - TODO confirm https for url

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
    expr = r'(http|https.*|\/.*\/[^\s\\]*)'
    return re.sub(expr, f'{palette[color]}\\1{reset}', str(s))


def get_stacktrace() -> str:
    return '\n'.join(traceback.format_stack()[:-1])  # remove this function


def save_stacktrace(fname: str = 'traceback') -> None:
    tb_text = get_stacktrace()
    with open(f'{fname}.txt', 'w') as file:
        file.write(tb_text)


def print_stacktrace():
    colorizer = Colorizer(style='jayme')
    lexer = pygments.lexers.get_lexer_by_name('pytb', stripall=True)
    tb_colored = pygments.highlight(get_stacktrace(), lexer, colorizer.formatter)
    print(tb_colored)
