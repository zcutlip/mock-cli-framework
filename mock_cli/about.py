from . import (
    __version__,
    __title__
)


class MockCLIAbout:

    def __str__(self):
        return f"{__title__} version {__version__}"
