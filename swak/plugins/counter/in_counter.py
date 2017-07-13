from __future__ import print_function

import click

from swak.plugin import BaseInput


class Counter(BaseInput):

    def __init__(self, max, field, delay):
        super(Counter, self).__init__()
        self.max = max
        self.field = field
        self.delay = delay
        self.count = 0

    def read(self):
        self.count += 1
        yield self.count


@click.command(help="Emit incremental number.")
@click.option('--max', default=10, show_default=True, help="Maximum count to emit.")
@click.option('--field', default=1, show_default=True, help="Number of count fields.")
@click.option('--delay', default=1, show_default=True, help="Delay seconds before next count.")
@click.option('--server', '-s', multiple=True, help="Servers.")
@click.pass_context
def main(ctx, max, field, delay):
    return Counter(max, field, delay)


if __name__ == '__main__':
    main()
