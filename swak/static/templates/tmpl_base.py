from __future__ import absolute_import
"""This module implements Swak {{type_name}} plugin of {{class_name}}."""  # NOQA

import click

from swak.plugin import {{base_name}}

class {{class_name}}({{base_name}}):
    """{{class_name}} class."""
{% block class_body %}{% endblock %}

@click.command(help="PLUGIN HELP MESSAGE GOES HERE")
@click.pass_context
def main(ctx):
    """Plugin entry."""
    return {{class_name}}()


if __name__ == '__main__':
    main()
