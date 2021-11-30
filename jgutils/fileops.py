import pickle
import shutil
from pathlib import Path


def check_path(p: Path) -> Path:
    """Create path if doesn't exist"""
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
    with open(check_path(p), 'wb') as file:
        pickle.dump(obj, file)

    return p


def load_pickle(p: Path) -> object:
    """Load pickle from file"""
    with open(p, 'rb') as file:
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
