"""This module implements Swak {{type_name}} plugin of {{class_name}}."""

import click

from swak.plugin import BaseModifier


class {{class_name}}(BaseModifier):
    """{{class_name}} class."""

    def prepare_for_stream(self, tag, es):
        """Prepare to modify an event stream.

        Args:
            tag (str): Event tag
            es (EventStream): Event stream
        """
        pass

    def modify(self, tag, time, record):
        """Modify an event.

        Args:
            tag (str): Event tag
            time (float): Event time
            record (dict): Event record

        Returns:
            If modified
                float: Modified time
                record: Modified record

            If removed
                None
        """
        raise NotImplemented()


@click.command(help="PLUGIN HELP MESSAGE GOES HERE")
@click.pass_context
def main(ctx):
    """Plugin entry."""
    return {{class_name}}()


if __name__ == '__main__':
    main()
