from __future__ import absolute_import  # NOQA
"""This module implements Swak input plugin of Dummy."""

import click

from swak.plugin import RecordInput


class Dummy(RecordInput):
    """Dummy class."""

    def __init__(self, record, max_count=3):
        """Init.

        Args:
            record (dict): A user input record.
            max_count (int): Maximum count to input.
        """
        super(RecordInput, self).__init__()
        self.record = record
        self.max_count = max_count
        self.count = 0

    def generate_record(self):
        """Generate records.

        Note: This function can be written in synchronous or asynchronous
         manner. But flushing with time interval does not work if this function
         is blocking. To guarantee flushing with time interval work, return an
         empty record in blocking situations.

        Yields:
            dict: A record.
        """
        for i in range(self.max_count):
            yield self.record


@click.command(help="Generate user input as dummy event.")
@click.argument('record')
@click.option('-c', '--count', help="Counter to repeat dummy record.")
@click.pass_context
def main(ctx, record, count):
    """Plugin entry."""
    return Dummy(record, count)


if __name__ == '__main__':
    main()
