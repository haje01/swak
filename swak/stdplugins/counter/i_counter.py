"""Counter input plugin module."""
from __future__ import print_function, absolute_import
import time

import click

from swak.plugin import RecordInput


class Counter(RecordInput):
    """Counter input plugin class."""

    def __init__(self, count, field, delay):
        """Init.

        Args:
            count: Count to read.
            field: Field count.
            delay: Delay time in seconds before next read.
        """
        super(Counter, self).__init__()
        self.count = count
        self.field = field
        self.delay = delay

    def generate_records(self):
        """Yield multiple records.

        Yields:
            dict
        """
        cnt = 0
        while True:
            if cnt >= self.count:
                break
            cnt += 1
            record = {}
            for f in range(self.field):
                key = "f{}".format(f + 1)
                record[key] = cnt
            yield record
            time.sleep(self.delay)


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
