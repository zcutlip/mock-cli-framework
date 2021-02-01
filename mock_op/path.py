import os
from pathlib import Path, _windows_flavour, _posix_flavour
from abc import abstractclassmethod


class AbstractPath(Path):
    _flavour = _windows_flavour if os.name == 'nt' else _posix_flavour

    @abstractclassmethod
    def __new__(cls, *args, **kwargs):
        return super().__new__(*args, **kwargs)

    @classmethod
    def _setup_file_path(cls, dirname, fname=None, create=False) -> Path:
        if fname:
            outpath = Path(dirname, fname)
        else:
            outpath = Path(dirname)
        if create:
            os.makedirs(dirname, exist_ok=True)
            if fname:
                Path.touch(outpath)
        return outpath


class ActualPath(AbstractPath):
    def __new__(cls, dirname, fname=None, create=False):
        dirname = os.path.expanduser(dirname)
        dirname = os.path.abspath(dirname)
        dirname = os.path.realpath(dirname)
        outpath = cls._setup_file_path(dirname, fname=fname, create=create)
        return super().__new__(cls, outpath)
