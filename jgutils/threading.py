import multiprocessing
import threading
import time
from collections.abc import Callable
from collections.abc import Generator
from collections.abc import Iterable
from queue import Queue
from threading import Thread
from typing import TYPE_CHECKING
from typing import Any
from typing import Literal
from typing import Self
from typing import overload

from joblib import Parallel
from joblib import delayed
from tqdm import tqdm

from jgutils import config as cf
from jgutils import utils as utl
from jgutils.errors import ExpectedError
from jgutils.logger import get_log

if TYPE_CHECKING:
    from jgutils.typing import Listable


log = get_log(__name__)


class ErrThread(Thread):
    """Thread to catch and raise errors in the parent thread"""

    def __init__(self, target: Callable, args: list[Any] | None = None, kwargs: dict | None = None):
        self.exc = None

        args = args or []
        kwargs = kwargs or {}

        def new_target():
            try:
                target(*args, **kwargs)
            except Exception as e:
                self.exc = e

        super().__init__(target=new_target)

    def join(self):
        threading.Thread.join(self)
        if self.exc:
            raise self.exc


class ThreadManager():

    def __init__(
            self,
            func: Callable[..., Any],
            items: list[dict] | Iterable[Any],
            raise_errors: bool = True,
            log_errors: bool = False,
            allowed_errors: 'Listable[type[Exception]] | None' = None,
            warn_expected: bool = True,
            dict_args: bool = True,
            func_kw: dict | None = None,
            use_tqdm: bool = True,
            n_jobs: int = 20,
            backend: str | None = 'threading',
            _log: bool = False):
        """Thread manager to manage calling a single function with multiple sets of arguments.

        Parameters
        ----------
        func : Callable[... | Any, str]
            Function to call. If string, will do getattr on items in items.
        items : Union[list[dict], Iterable[Any]]
            List of arguments to pass to func.
            If dict_args is True, will assume each item is a dict of arguments to unpack.
        raise_errors : bool, optional
            Raise errors, or log.warning and continue, by default True
        log_errors : bool, optional
            Log errors, by default False
        allowed_errors : Listable[type[Exception]] | None, optional
            List of errors to allow (if raise_errors is True), by default None
        warn_expected : bool, optional
            Show warning on expected errors, by default True
        dict_args : bool, optional
            If True, unpack items to func, else pass single in items as item to func
        func_kw : dict | None, optional
            Static keyword arguments to pass to func (if str func), by default None
        use_tqdm : bool, optional
            Use tqdm to show progress, by default True
        n_jobs : int, optional
            Number of threads to use (only works with .run not .start), by default 50
        backend : str | None, optional
            Backend to use for joblib, by default 'threading' - pass None to use default
        _log : bool, optional
            Show log message, by default False
        """

        self.func = func
        self.items = items
        self.threads = []  # type: list[Thread]
        self.queue = Queue()
        self._log = _log

        # TODO bit messy for now, combining native thread + Parallel/tqdm in one class
        self.raise_errors = raise_errors
        self.log_errors = log_errors
        self.allowed_errors = utl.as_list(allowed_errors)
        self.warn_expected = warn_expected
        self.allowed_errors.append(ExpectedError)

        self.backend = backend

        if self.backend == 'threading':
            # 10 jobs, 5 items = 5 jobs
            self.n_jobs = min(n_jobs, max(len(items), 1))
        else:
            # process based, so use all available
            self.n_jobs = n_jobs = min(multiprocessing.cpu_count(), len(items))

        self.dict_args = dict_args  # define wether to unpack dict args or not
        self.func_kw = func_kw or {}
        self.use_tqdm = use_tqdm if not cf.IS_REMOTE and _log else False

    @overload
    def start(self, wait: Literal[True], _log: bool = False) -> list[Any]:
        ...

    @overload
    def start(self, wait: Literal[False], _log: bool = False) -> 'ThreadManager':
        ...

    def start(self, wait: bool = True, _log: bool = False) -> 'ThreadManager | list[Any]':
        """Start all threads."""

        for m in self.items:
            thread = ErrThread(target=lambda q, kw, m=m: q.put(
                self.func(**m)), args=[self.queue, m])
            self.threads.append(thread)
            thread.start()

        if wait:
            start = time.time()
            res = self.results()
            end = time.time()

            if _log:
                log.info(
                    f'Finished {len(self.threads)} threads in {end - start:.2f} seconds')

            return res

        return self

    def start_sequential(self, _log: bool = True) -> list[Any]:
        """Execute functions sequentially for testing

        Returns
        -------
        list[Any]
            List of results from each thread.
        """
        start = time.time()
        results = [self.func(**m) for m in self.items]
        end = time.time()

        if _log:
            log.info(
                f'Finished {len(results)} functions in {end - start:.2f} seconds')

        return results

    def results(self) -> list[Any]:
        """Join all threads and get result value from functions

        Returns
        -------
        list[Any]
            List of results from each thread.
        """
        results = []

        # wait for all threads to finish
        for thread in self.threads:
            thread.join()

        # get results from queue
        for _ in range(len(self.threads)):
            results.append(self.queue.get())

        return results

    def err_wrapper(self, func: Callable[..., Any]) -> Callable[..., Any]:
        """Wrapper to catch errors and log
        - NOTE only used for Parallel/tqdm implementation for now
        """
        def wrapper(*args, **kwargs) -> Any:  # noqa: ANN401
            try:
                return func(*args, **kwargs)
            except Exception as e:
                err_name = e.__class__.__name__
                func_name = getattr(func, '__name__', repr(func))

                if any(isinstance(e, err) for err in self.allowed_errors):
                    if self.warn_expected:
                        log.warning(f'[Expected Error: {err_name}] {e}')
                elif self.raise_errors:
                    max_len = 500
                    err_msg = str(e)[:max_len]
                    log.warning(
                        f'[{err_name}] Failed: "{func_name}" with: '
                        + f'args={str(args)[:max_len]}, kw={str(kwargs)[:max_len]}, {err_msg}')

                    raise e

                elif self.log_errors:
                    log.error(f'[{err_name}] Thread Error "{func_name}": {e}')
                else:
                    log.warning(f'[{err_name}] Thread Error "{func_name}": {e}')

        return wrapper

    def run(self, return_none: bool = False) -> list[Any]:
        """Call with ProgressParallel/tqdm

        Parameters
        ----------
        return_none : bool, optional
            If False, don't return any None values, by default False

        Returns
        -------
        list[Any]
            List of results from each thread.
        """
        # NOTE could try getting rid of delayed here and use functools.partial instead

        if isinstance(self.func, str):
            # assume calling func as method on items in items
            job = (delayed(self.err_wrapper(getattr(item, self.func)))
                   (**self.func_kw) for item in self.items)

        elif self.dict_args:
            # unpack dict args to func
            job = (delayed(self.err_wrapper(self.func))(**item)
                   for item in self.items)

        else:
            # call func with single item as arg
            job = (delayed(self.err_wrapper(self.func))(item)
                   for item in self.items)

        res = ProgressParallel(
            n_jobs=self.n_jobs,
            verbose=0,
            backend=self.backend,
            items=self.items,
            use_tqdm=self.use_tqdm,
            _log=self._log)(job)  # type: list[Any]

        # remove any None values
        if not return_none:
            res = [r for r in res if not r is None]

        return res


class ProgressParallel(Parallel):
    """Show Parallel task with tqdm progress bar

    NOTE this should be used for local operations only for now
    """

    def __init__(
            self,
            use_tqdm: bool = True,
            total: int | None = None,
            items: Iterable[Any] | None = None,
            _log: bool = False,
            *args, **kwargs):

        self._use_tqdm = use_tqdm if not cf.SYS_FROZEN else False
        self._total = total
        self._log = _log

        if not items is None:
            self._total = len(items)

        # limit bar width in terminal
        self.bar_format = '{l_bar}{bar:20}{r_bar}{bar:-20b}'

        if cf.SYS_FROZEN:
            kwargs['verbose'] = 0  # disable verbose output when frozen

        super().__init__(*args, **kwargs)

    @classmethod
    def thread(cls, *args, **kw) -> Self:
        """Convenience method to create threadded parallel object with defaults:
        - n_jobs = 50 (arbitrary)
        - backend = 'threading'

        - NOTE not sure if eg 50 threads is necessarily faster or if there is a limit somewhere
        """

        default_kw = dict(
            n_jobs=50,
            backend='threading',
            verbose=6)

        # update defaults with kw passed in
        kw = {**default_kw, **kw}

        return cls(*args, **kw)

    def __call__(self, *args, **kwargs) -> Generator:
        if self._log:
            log.info(
                f'Starting tasks={self._total:,.0f} with n_jobs={self.n_jobs}')

        # TODO would be nice to capture tqdm output and only show at bottom of terminal

        with tqdm(
                disable=not self._use_tqdm,
                total=self._total,
                bar_format=self.bar_format) as self._pbar:
            return Parallel.__call__(self, *args, **kwargs)

    def print_progress(self):
        if self._total is None:
            self._pbar.total = self.n_dispatched_tasks

        self._pbar.n = self.n_completed_tasks
        self._pbar.refresh()

    def _print(self, *args):
        """Just to suppress joblib.Parallel print output"""
        pass
