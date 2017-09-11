"""Stdout module."""
from __future__ import print_function, absolute_import

import json

import click

from swak.plugin import Output


class Stdout(Output):
    """Stdout class."""

    def write_stream(self, tag, es):
        """Write event stream."""
        for time, record in es:
            print("{}\t{}\t{}".format(time, tag, json.dumps(record)))


@click.command(help="Output to standard output.")
def main():
    """Plugin entry."""
    return Stdout()


if __name__ == '__main__':
    main()
