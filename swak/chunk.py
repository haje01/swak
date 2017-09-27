"""This module implements chunk."""


class Chunk(object):
    """Chunk class."""

    def __init__(self, binary):
        """Init.

        Args:
            binary(bool): Whether store data as binary or not.
        """
        self.binary = binary
        self.total_bytes = 0

    @property
    def bytesize(self):
        """Return chunk size in byte."""
        assert self.binary, "Require data in binary format."
        return self.total_bytes
