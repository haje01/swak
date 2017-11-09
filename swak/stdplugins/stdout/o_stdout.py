"""Stdout module."""
from __future__ import print_function, absolute_import

import logging

import click

from swak.plugin import Output
from swak.formatter import Formatter, StdoutFormatter
from swak.buffer import Buffer
from swak.memorybuffer import MemoryBuffer, DEFAULT_CHUNK_MAX_RECORD,\
    DEFAULT_CHUNK_MAX_SIZE, DEFAULT_BUFFER_MAX_CHUNK


class Stdout(Output):
    """Stdout class."""

    def __init__(self, formatter=None, abuffer=None):
        """Init.

        Args:
            formatter (Formatter): Swak formatter for this output.
            abuffer (Buffer): Swak buffer for this output.
        """
        logging.info("Stdout.__init__")
        formatter = formatter if formatter is not None else StdoutFormatter()
        super(Stdout, self).__init__(formatter, abuffer)

    def _write(self, bulk):
        """Write a bulk.

        Args:
            bulk (bytearray or list): If the chunk that passes the argument is
              a binary type, bulk is an array of bytes, otherwise it is a list
              of strings.
        """
        logging.debug("Stdout._write")
        if type(bulk) is list:
            for line in bulk:
                print(line)
        else:
            print(bulk)


@click.group(chain=True, invoke_without_command=True,
             help="Output to standard output.")
@click.pass_context
def main(ctx):
    """Plugin entry."""
    pass


@main.resultcallback()
def process_components(components):
    """Process components and build a Stdout.

    Args:
        components (list)

    Returns:
        Stdout
    """
    _formatter = _buffer = None
    for com in components:
        if isinstance(com, Formatter):
            _formatter = com
        if isinstance(com, Buffer):
            _buffer = com
    return Stdout(_formatter, _buffer)


@main.command('f.stdout', help="Stdout formatter for this output.")
@click.option('-z', '--timezone', default=None, show_default=True,
              help="Timezone for format.")
def f_stdout(timezone):
    """Formatter entry."""
    return StdoutFormatter(timezone=timezone)


@main.command('b.memory', help="Memory buffer for this output.")
@click.option('-f', '--flush-interval', default=None, type=str,
              show_default=True, help="Flush interval.")
@click.option('-r', '--chunk-max-record', default=DEFAULT_CHUNK_MAX_RECORD,
              type=int, show_default=True, help="Maximum records per chunk.")
@click.option('-s', '--chunk-max-size', default=DEFAULT_CHUNK_MAX_SIZE,
              show_default=True, help="Maximum chunks per buffer.")
@click.option('-c', '--buffer-max-chunk', default=DEFAULT_BUFFER_MAX_CHUNK,
              show_default=True, help="Maximum chunks per buffer.")
def b_memory(flush_interval, chunk_max_record, chunk_max_size,
             buffer_max_chunk):
    """Formatter entry."""
    return MemoryBuffer(None, False, flush_interval=flush_interval,
                        buffer_max_chunk=buffer_max_chunk,
                        chunk_max_record=chunk_max_record)


if __name__ == '__main__':
    main()
