import os
import sys
from pathlib import Path
from typing import Optional, Union

try:
    from pathlib import _posix_flavour, _windows_flavour
except ImportError:
    pass
from abc import abstractclassmethod

# significant changes to pathlib in python >= 3.12
NEW_PATHLIB_MIN_PYTHON_VER = (3, 12)


class AbstractPath(Path):
    _new_style = True
    if sys.version_info < NEW_PATHLIB_MIN_PYTHON_VER:
        _new_style = False

    # previous to Python 3.12 you couldn't easily subclass pathlib.Path
    # to do so required this hack to set _flavour
    # but this explicitly does not work in 3.12
    if not _new_style:
        _flavour = _windows_flavour if os.name == 'nt' else _posix_flavour

    @abstractclassmethod
    def __new__(cls, *args):
        obj = super().__new__(*args)
        return obj

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
    def __new__(cls, dirname: Union[str, Path], fname: Optional[Union[str, Path]] = None, create: Optional[bool] = False):
        """
        Create a fully resolved absolute path object from a path name and optionally a filename.
        Optionally create the full path on the filesystem during initialization.

        Parameters
        ----------
        dirname : Union[str, Path]
            Main directory path. Will be parent of fname if provided
        fname : Union[str, Path], optional
            The name of a file to append to the directory path
        create : Optional[bool], optional
            Create the fully qualified directory path on the filesystem.
            If a filename is provided, the file will be touched on the filesystem, creating an empty file if none exists

        Returns
        -------
        ActualPath
            The fully resolved absolute path object
        """
        dirname = os.path.expanduser(dirname)
        dirname = os.path.abspath(dirname)
        dirname = os.path.realpath(dirname)
        outpath = cls._setup_file_path(dirname, fname=fname, create=create)
        obj = super().__new__(cls, outpath)

        return obj

    def __init__(self, dirname, fname=None, **kwargs):
        if self._new_style:
            # only call superclass __init__ on python >= 3.12
            args = [dirname]
            if fname is not None:
                args.append(fname)
            super().__init__(*args)
