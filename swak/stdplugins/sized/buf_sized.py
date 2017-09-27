from __future__ import absolute_import  # NOQA
"""This module implements Swak buffer plugin of Memory."""

import click

from swak.plugin import Buffer
from swak.util import time_value, size_value


class Sized(Buffer):
    """Buffer class in which chunks are sliced by size."""

    def __init__(self, binary, chunk_max_record, chunk_max_size,
                 buffer_max_chunk, buffer_max_size, flush_interval):
        """Init.

        Args:
            binary (bool): Store data as binary or not.
            chunk_max_record (int): Maximum records per chunk for slicing.
            chunk_max_size (str): Maximum chunk size for slicing with suffix.
            buffer_max_chunk (int): Maximum chunks per buffer for slicing.
            buffer_max_size (str): Maximum buffer size for slicing with suffix.
            flush_interval (str): Flush interval with time suffix.
        """
        super(Sized, self).__init__(binary)

        # validate argument
        if not binary and (chunk_max_size is not None or buffer_max_size is not
                           None):
            raise ValueError("Size arguments needs binary format.")

        chunk_max_size = size_value(chunk_max_size)
        buffer_max_size = size_value(buffer_max_size)
        flush_interval = time_value(flush_interval)

        self.queue = None
        self.max_record = 0

    def start(self):
        """Start buffer."""
        super(Sized, self).start()
        self.buffer = []

    def set_max_record(self, max_record):
        """Set maximum records number."""
        self.max_record = max_record

    def append(self, es):
        """Append event stream to buffer.

        Args:
            es (EventStream): Event stream.
        """
        self.buffer.append(es)
        if len(self.buffer) >= self.max_record:
            self.flush()


@click.command(help="Buffering by size sliced chunk.")
@click.option('-r', '--chunk-max-record', default=None, type=int,
              help="Maximum records per chunk for slicing.")
@click.option('-s', '--chunk-max-size', default='8m', show_default=True,
              help="Maximum chunk size for slicing.")
@click.option('-c', '--buffer-max-chunk', default=64, show_default=True,
              help="Maximum chunks per buffer for slicing.")
@click.option('-b', '--buffer-max-size', default='512m', show_default=True,
              help="Maximum buffer size for slicing.")
@click.option('-i', '--flush-interval', default='60s', show_default=True,
              help="Flushing interval.")
@click.pass_context
def main(ctx, binary, chunk_max_record, chunk_max_size, buffer_max_chunk,
         buffer_max_size, flush_interval):
    """Plugin entry."""
    return Sized(binary, chunk_max_record, chunk_max_size, buffer_max_chunk,
                 buffer_max_size, flush_interval)


if __name__ == '__main__':
    main()
