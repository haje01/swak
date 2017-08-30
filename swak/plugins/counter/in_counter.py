"""Counter input plugin module."""
from __future__ import print_function, absolute_import
import time

import click

from swak.plugin import BaseInput


class Counter(BaseInput):
    """Counter input plugin class."""

    def __init__(self, max, field, delay):
        """Init.

        Args:
            max: Maximum count to read.
            field: Maximum field count.
            delay: Delay time in seconds before next read.
        """
        super(Counter, self).__init__()
        self.maxcnt = max
        self.field = field
        self.delay = delay
        self.count = 0

    def read(self):
        """Read data from source.

        Yields:
            dict
        """
        cnt = 0
        while True:
            if cnt >= self.maxcnt:
                break
            cnt += 1
            self.count += 1
            record = {}
            for f in range(self.field):
                key = "f{}".format(f + 1)
                record[key] = self.count
            yield record
            time.sleep(self.delay)


@click.command(help="Generate incremental numbers.")
@click.option('--max', default=5, show_default=True, help="Maximum count to"
              " emit.")
@click.option('--field', default=1, show_default=True, help="Number of count"
              " fields.")
@click.option('--delay', default=0, show_default=True, help="Delay seconds"
              " before next count.")
@click.pass_context
def main(ctx, max, field, delay):
    """Plugin entry."""
    return Counter(max, field, delay)


if __name__ == '__main__':
    main()
