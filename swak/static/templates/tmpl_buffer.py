"""This module implements Swak {{type_name}} plugin of {{class_name}}."""

import click

from swak.plugin import BaseBuffer


class {{class_name}}(BaseBuffer):
    """{{class_name}} class."""

    def append(self, record):
        """Append a record."""
        raise NotImplemented()


@click.command(help="PLUGIN HELP MESSAGE GOES HERE")
@click.pass_context
def main(ctx):
    """Plugin entry."""
    return {{class_name}}()


if __name__ == '__main__':
    main()
