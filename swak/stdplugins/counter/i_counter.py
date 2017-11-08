"""Counter input plugin module."""
from __future__ import print_function, absolute_import
import time

import click
from six.moves import range

from swak.plugin import RecordInput


class Counter(RecordInput):
    """Counter input plugin class."""

    def __init__(self, max_count, field, delay):
        """Init.

        Args:
            max_count: Maximum count..
            field: Field count.
            delay: Delay time in seconds before next read.
        """
        super(Counter, self).__init__()
        self.max_count = max_count
        self.field = field
        self.delay = delay
        self.last_time = None

    def generate_record(self):
        """Generate records.

        Note: Don't do blocking operation. return an empty dict in inadequate
            situations.

        Yields:
            dict: A record
        """
        last_time = None
        for idx in range(self.max_count):
            cur_time = time.time()
            if last_time is None:
                last_time = cur_time
            if not (self.delay is None or self.delay == 0):
                if cur_time - last_time < self.delay:
                    yield {}

            record = {}
            for f in range(self.field):
                key = "f{}".format(f + 1)
                record[key] = idx + 1
            last_time = cur_time
            yield record


@click.command(help="Generate incremental numbers.")
@click.option('-c', '--count', default=3, show_default=True, help="Count to "
              "emit.")
@click.option('-f', '--field', default=1, show_default=True, help="Count of "
              "fields.")
@click.option('-d', '--delay', default=0.0, show_default=True, help="Delay "
              "seconds before next count.")
@click.pass_context
def main(ctx, count, field, delay):
    """Plugin entry."""
    return Counter(count, field, delay)


if __name__ == '__main__':
    main()
