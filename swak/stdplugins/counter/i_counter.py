"""Counter input plugin module."""
from __future__ import print_function, absolute_import
import time

import click
from six.moves import range

from swak.plugin import RecordInput
# from swak.data import MultiDataStream

YIELD_STEP = 10

DEFAULT_NUMBER = 3
DEFAUTL_FIELD = 1
DEFAULT_DELAY = 0


class Counter(RecordInput):
    """Counter input plugin class.

    Output number of count.
    """

    def __init__(self, number=DEFAULT_NUMBER, field=DEFAUTL_FIELD,
                 delay=DEFAULT_DELAY):
        """Init.

        Args:
            number (int): Number to count.
            field (int): Field number.
            delay: Delay time in seconds before next read.
        """
        super(Counter, self).__init__()
        self.number = number
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
        last_time = time.time()
        for idx in range(self.number):
            record = {}
            for f in range(self.field):
                key = "f{}".format(f + 1)
                record[key] = idx + 1
            last_time = time.time()
            yield record

            if not (self.delay is None or self.delay == 0):
                # wait delay
                while True:
                    diff = time.time() - last_time
                    if diff < self.delay:
                        yield {}
                    else:
                        break

    # def generate_stream(self, gen_data, stop_event):
    #     """Generate data stream from data generator.

    #     Args:
    #         gen_data (function): Data generator function.
    #         stop_event (threading.Event): Stop event

    #     Yields:
    #         tuple: (tag, DataStream)
    #     """
    #     times = []
    #     datas = []
    #     for i, event in enumerate(gen_data(stop_event)):
    #         utime, data = event
    #         times.append(utime)
    #         datas.append(data)
    #         if i % YIELD_STEP == 0:
    #             yield self.tag, MultiDataStream(times, datas)
    #             times = []
    #             datas = []
    #     # yield remain data
    #     yield self.tag, MultiDataStream(times, datas)


@click.command(help="Generate incremental numbers.")
@click.option('-n', '--number', default=DEFAULT_NUMBER, show_default=True,
              help="Number to emit.")
@click.option('-f', '--field', default=DEFAUTL_FIELD, show_default=True,
              help="Number of fields.")
@click.option('-d', '--delay', default=DEFAULT_DELAY, show_default=True,
              help="Delay seconds before next count.")
@click.pass_context
def main(ctx, number, field, delay):
    """Plugin entry."""
    return Counter(number, field, delay)


if __name__ == '__main__':
    main()
