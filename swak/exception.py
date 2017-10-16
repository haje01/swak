"""This module implements plugin base."""


class UnsupportedPython(Exception):
    """Exception: Unsupported version of python."""

    pass


class NoMoreData(Exception):
    """Exception: No more data for this input."""

    pass
