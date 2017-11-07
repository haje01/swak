"""This module implements plugin base."""


class UnsupportedPython(Exception):
    """Exception: Unsupported version of python."""

    pass


# class InputClosed(Exception):
#     """Exception: No more data for this input."""

#     pass


class ConfigError(Exception):
    """Exception: Config has an error."""

    pass


class GracefulExit(Exception):
    """Exception for graceful exit."""

    pass
