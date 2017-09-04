"""Stdout module."""
from __future__ import print_function, absolute_import

import click

from swak.plugin import BaseOutput
from swak.const import TEST_STREAM_TAG


class Stdout(BaseOutput):
    """Stdout class."""

    def write_stream(self, tag, es):
        """Write event stream."""
        for time, record in es:
            stag = '' if tag == TEST_STREAM_TAG else "tag: {}, ".format(tag)
            print("{}time: {}, record: {}".format(stag, time, record))


@click.command(help="Output to standard output.")
def main():
    """Plugin entry."""
    return Stdout()


if __name__ == '__main__':
    main()
