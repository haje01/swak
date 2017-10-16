"""Counter input plugin module."""
from __future__ import print_function, absolute_import
import time

import click

from swak.plugin import RecordInput
from swak.exception import NoMoreData


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
        self.count = 0
        self.max_count = max_count
        self.field = field
        self.delay = delay
        self.last_time = None

    def read_record(self):
        """Generate a record from the source.

        Raises:
            NoMoreData: No more data to generate.

        Returns:
            dict: Generated record. Return empty dict if conditions do not
                match.
        """
        if self.count >= self.max_count:
            raise NoMoreData()

        cur_time = time.time()
        if self.last_time is None:
            self.last_time = cur_time
        if not (self.delay is None or self.delay == 0):
            if time.time() - self.last_time < self.delay:
                return {}

        self.count += 1
        record = {}
        for f in range(self.field):
            key = "f{}".format(f + 1)
            record[key] = self.count
        self.last_time = cur_time
        return record


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
