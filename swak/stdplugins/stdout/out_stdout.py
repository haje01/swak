"""Stdout module."""
from __future__ import print_function, absolute_import

import click

from swak.plugin import BaseOutput


class Stdout(BaseOutput):
    """Stdout class."""

    def process(self, tag, es):
        """Process event stream."""
        stag = '' if len(tag) == 0 else "tag: {}, ".format(tag)
        for time, record in es:
            print("{}time: {}, record: {}".format(stag, time, record))


@click.command(help="Output to standard output.")
def main():
    """Plugin entry."""
    return Stdout()


if __name__ == '__main__':
    main()
