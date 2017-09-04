"""This module implements Swak {{type_name}} plugin of {{class_name}}."""

import click

from swak.plugin import BaseInput


class {{class_name}}(BaseInput):
    """BaseInput class."""

    def __init__(self):
        """Init."""
        super(BaseInput, self).__init__()
        self.filter_fn = None

    def read(self):
        """Read data from source.

        It is implemented in the following format.

        1. Read the line-delimited text from the source.
        2. If the ``encoding`` is specified, convert it to ``utf8`` text.
        3. Separate text by new line,
        4. Filter lines if filter function exists.
        5. Yield them. If this is an input plugin for data of a known type,
           such as ``syslog``, it shall parse itself and return the record,
           otherwise it will just return the line.

        """
        raise NotImplemented()


@click.command(help="PLUGIN HELP MESSAGE GOES HERE")
@click.pass_context
def main(ctx):
    """Plugin entry."""
    return {{class_name}}()


if __name__ == '__main__':
    main()
