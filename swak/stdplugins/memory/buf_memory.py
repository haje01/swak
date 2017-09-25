from __future__ import absolute_import  # NOQA
"""This module implements Swak buffer plugin of Memory."""

import click

from swak.plugin import Buffer


class Memory(Buffer):
    """Memory class."""

    def __init__(self):
        """Init."""
        self.queue = None
        self.max_record = 0

    def start(self):
        """Start buffer."""
        super(Memory, self).start()
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


@click.command(help="Buffer events in memory.")
@click.option('-m', '--max-event', default=0, show_default=True,
              help="Maximum events before flushing. 0 means immediate"
                   " flushing.")
@click.pass_context
def main(ctx, max_event):
    """Plugin entry."""
    return Memory(max_event)


if __name__ == '__main__':
    main()
