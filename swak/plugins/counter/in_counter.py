from __future__ import print_function, absolute_import

import click

from swak.plugin import BaseInput


class Counter(BaseInput):

    def __init__(self, max, field, delay):
        super(Counter, self).__init__()
        self.maxcnt = max
        self.field = field
        self.delay = delay
        self.count = 0
        self.last_read = 0

    def read(self):
        cur_time = time.time()
        if cur_time - self.read_time >= self.delay:
            self.count += 1
            self.last_read = cur_time
            values = [self.count] * self.field


@click.command(help="Generate incremental numbers.")
@click.option('--max', default=10, show_default=True, help="Maximum count to"
              " emit.")
@click.option('--field', default=1, show_default=True, help="Number of count"
              " fields.")
@click.option('--delay', default=1, show_default=True, help="Delay seconds"
              " before next count.")
@click.pass_context
def main(ctx, max, field, delay):
    return Counter(max, field, delay)


if __name__ == '__main__':
    main()
