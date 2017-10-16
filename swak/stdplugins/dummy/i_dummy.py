from __future__ import absolute_import  # NOQA
"""This module implements Swak input plugin of Dummy."""

import click

from swak.plugin import RecordInput
from swak.exception import NoMoreData


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

    def read_record(self):
        """Generate a record from the source.

        Throw NoMoreData exception if no more record available.

        Raises:
            NoMoreData: No more data to generate.

        Returns:
            dict: Generated record. Return empty dict if conditions do not
                match.
        """
        if self.count < self.max_count:
            self.count += 1
            return self.record
        else:
            raise NoMoreData()


@click.command(help="Generate user input as dummy event.")
@click.argument('record')
@click.option('-c', '--count', help="Counter to repeat dummy record.")
@click.pass_context
def main(ctx, record, count):
    """Plugin entry."""
    return Dummy(record, count)


if __name__ == '__main__':
    main()
