"""Stdout module."""
from __future__ import print_function, absolute_import

import json

import click

from swak.plugin import BaseOutput


class Stdout(BaseOutput):
    """Stdout class."""

    def write_stream(self, tag, es):
        """Write event stream."""
        for time, record in es:
            print(json.dumps((tag, time, record)))


@click.command(help="Output to standard output.")
def main():
    """Plugin entry."""
    return Stdout()


if __name__ == '__main__':
    main()
