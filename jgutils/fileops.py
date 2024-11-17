import pickle
import shutil
from datetime import datetime as dt
from datetime import timedelta as delta
from pathlib import Path
from typing import Any


def check_path(p: Path | str) -> Path:
    """Create path if doesn't exist

    Returns
    -------
    Path
        Path checked
    """
    if isinstance(p, str):
        p = Path(p)

    p_create = p if p.is_dir() or not '.' in p.name else p.parent

    # if file, create parent dir, else create dir
    if not p_create.exists():
        p_create.mkdir(parents=True)

    return p


def clean_dir(p: Path) -> None:
    """Clean all saved models in models dir"""
    if p.is_dir():
        for _p in p.glob('*'):
            _p.unlink()


def save_pickle(obj: object, p: Path, name: str) -> Path:
    """Save object to pickle file

    Parameters
    ----------
    obj : object
        object to save as pickle
    p : Path
        base dir to save in
    name : str
        file name (excluding .pkl)

    Returns
    -------
    Path
        path of saved file
    """
    p = p / f'{name}.pkl'
    with check_path(p).open('wb') as file:
        pickle.dump(obj, file)

    return p


def load_pickle(p: Path) -> Any:  # noqa: ANN401
    """Load pickle from file"""
    with p.open('rb') as file:
        return pickle.load(file)


def unzip(p: Path, p_dst: Path = None, delete: bool = False) -> Path:
    """Simple wrapper for shultil unpack_archive with default unzip dir

    Parameters
    ----------
    p : Path
        File to unzip
    p_dst : Path, optional
        Unzip in different dir, by default parent dir
    delete : bool, optional
        Delete original zip after unpack, by default False
    """
    if p_dst is None:
        p_dst = p.parent

    shutil.unpack_archive(p, p_dst)

    if delete:
        p.unlink()

    return p


def date_created(p: Path) -> dt:
    """Get date from folder date created

    Parameters
    ----------
    p : Path
        Folder path to check

    Returns
    -------
    dt
        date created
    """
    return dt.fromtimestamp(p.stat().st_birthtime)


def date_modified(p: Path) -> dt:
    """Get date file/folder modified

    Parameters
    ----------
    p : Path
        file/folder path to check

    Returns
    -------
    dt
        date modified
    """
    return dt.fromtimestamp(p.stat().st_mtime)


def older_than(p: Path, minutes: int) -> bool:
    """Check if file/folder is older than x minutes OR doesn't exist

    Parameters
    ----------
    p : Path
        file/folder path to check
    minutes : int
        minutes to check against

    Returns
    -------
    bool
        if file/folder is older than minutes
    """
    if not p.exists():
        return True

    return date_modified(p) < dt.now() + delta(minutes=-minutes)
