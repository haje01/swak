"""This module implements Swak {{type_name}} plugin of {{class_name}}."""

import click

from swak.plugin import BaesParser


class {{class_name}}(BaseParser):
    """{{class_name}} class."""

    def parse(self):
        """Parse."""
        raise NotImplemented()


@click.command(help="PLUGIN HELP MESSAGE GOES HERE")
@click.pass_context
def main(ctx):
    """Plugin entry."""
    return {{class_name}}()


if __name__ == '__main__':
    main()
