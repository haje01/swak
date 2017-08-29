"""Reform: A modifier plugin."""

import click

from swak.plugin import BaseModifier


class Reform(BaseModifier):
    """Reform class."""

    def __init__(self, adds, dels):
        """Init.

        Args:
            adds (list): List of (key, value) tuple to add.
            dels (list): List of key to delete.
        """
        self.adds = adds
        self.dels = dels

    def modify(self, tag, time, record, placeholders):
        """Modify am event by modifying.

        If adds & dels conflicts, deleting key wins.

        Args:
            tag (str): Event tag
            time (float): Event time
            record (dict): Event record
            placeholders (dict): Placeholder value reference.

        Returns:
            float: Modified time
            record: Modified record
        """
        for key, val in self.adds:
            placeholders['time'] = time
            placeholders['record'] = record
            record[key] = self.expand(val, placeholders)

        for key in self.dels:
            del record[key]

        return time, record

    def expand(self, val, placeholder_values):
        """Expand value string with placeholders.

        Args:
            val (str): A string value with possible placeholder.
            placeholder_values (dict): Placeholder value reference.

        Returns:
            dict: Expanded value
        """
        pass


@click.command(help="Add, delete, overwrite record field.")
@click.option('-a', '--add', "adds", type=(str, str), multiple=True,
              help="Add new key / value pair.")
@click.option('-d', '--del', "dels", type=str, multiple=True,
              help="Delete existing key / value pair by key.")
def main(adds, dels):
    """Plugin entry for CLI."""
    return Reform(adds, dels)


if __name__ == '__main__':
    main()
