from __future__ import absolute_import  # NOQA
"""This module implements Swak input plugin of Dummy."""

import click

from swak.plugin import RecordInput


class Dummy(RecordInput):
    """Dummy class."""

    def __init__(self, record, count=1):
        """Init.

        Args:
            record (dict): A user input record.
            count (int): Repeat count.
        """
        super(RecordInput, self).__init__()
        self.record = record
        self.count = count

    def generate_records(self):
        """Return multiple records.

        Yields:
            dict: A record
        """
        for i in range(self.count):
            yield self.record


@click.command(help="Generates user input as dummy event.")
@click.argument('record')
@click.option('-c', '--count', help="Counter to repeat dummy record.")
@click.pass_context
def main(ctx, record, count):
    """Plugin entry."""
    return Dummy(record, count)


if __name__ == '__main__':
    main()
