"""Stdout module."""
from __future__ import print_function, absolute_import

import click

from swak.plugin import Output
from swak.formatter import Formatter, StdoutFormatter
from swak.buffer import MemoryBuffer


class Stdout(Output):
    """Stdout class."""

    def __init__(self, formatter=None, abuffer=None):
        """Init.

        Args:
            formatter (Formatter): Swak formatter for this output.
            abuffer (Buffer): Swak buffer for this output.
        """
        formatter = formatter if formatter is not None else StdoutFormatter()
        if abuffer is None:
            abuffer = MemoryBuffer(self, False, 1, 1)
        super(Stdout, self).__init__(formatter, abuffer)

    def _write(self, bulk):
        """Write a bulk."""
        print(bulk)


@click.group(chain=True, invoke_without_command=True,
             help="Output to standard output.")
@click.pass_context
def main(ctx):
    """Plugin entry."""
    pass


@main.resultcallback()
def process_components(components):
    """Process components and build Stdout.

    Args:
        components (list)

    Returns:
        Stdout
    """
    _formatter = None
    for com in components:
        if isinstance(com, Formatter):
            _formatter = com
    return Stdout(_formatter)


@main.command('f.stdout', help="Setting formatter for this output.")
@click.option('-z', '--timezone', default="UTC", show_default=True,
              help="Timezone for format.")
def f_stdout(timezone):
    """Formatter entry."""
    return StdoutFormatter(timezone=timezone)


if __name__ == '__main__':
    main()
