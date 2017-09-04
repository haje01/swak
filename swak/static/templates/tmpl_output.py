"""This module implements Swak {{type_name}} plugin of {{class_name}}."""

import click

from swak.plugin import BaseOutput


class {{class_name}}(BaseOutput):
    """{{class_name}} class."""

    def write_stream(self, tag, es):
        """Write event stream synchronously.

        Args:
            tag (str): Event tag.
            es (EventStream): Event stream.
        """
        raise NotImplemented()

    def write_chunk(self, chunk):
        """Write a chunk from buffer."""
        raise NotImplemented()


@click.command(help="PLUGIN HELP MESSAGE GOES HERE")
@click.pass_context
def main(ctx):
    """Plugin entry."""
    return {{class_name}}()


if __name__ == '__main__':
    main()
