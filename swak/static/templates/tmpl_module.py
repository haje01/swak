"""This module implements Swak {{type_name}} plugin of {{class_name}}."""

import click

from swak.plugin import {{base_name}}


class {{class_name}}({{base_name}}):
    """{{class_name}} class."""
{% if type_name == 'input' %}
    input impl
{% elif type_name == 'parser' %}
    parser impl
{% endif %}

@click.command(help="PLUGIN HELP MESSAGE GOES HERE")
@click.pass_context
def main(ctx):
    """Plugin entry."""
    return {{class_name}}()


if __name__ == '__main__':
    main()
