from __future__ import absolute_import  # NOQA
"""This module implements Swak {{type_name}} plugin of {{class_name}}."""

import click

from swak.plugin import {{base_name}}
{% if 'Input' in base_name%}from swak.exception import NoMoreData{%endif%}
{% block import_body %}{% endblock %}

class {{class_name}}({{base_name}}):
    """{{class_name}} class."""

    def __init__(self):
        """Init class."""
        super({{class_name}}, self).__init__()

    def _start(self):
        """Start plugin.

        This method is called when the task starts after processing the
        setting. Creation of resources such as files and threads to be used in
        the plug-in is created here.
        """
        # Allocate resources if necessary.

    def _stop(self):
        """Stop plugin.

        This method is called when the task is preparing to shutdown. You
        should do simple things that do not fail, such as setting a thread
        stop flag.
        """
        pass

    def _shutdown(self):
        """Shutdown plugin.

        This method is called when the task is completely shutdown. Here you
        can close or remove any files, threads, etc. that you had created in
        ``start``.
        """
        # Release resources if necessary.
    {% block class_body %}{% endblock %}
{% block cmd_body  %}{% endblock %}

@click.command(help="PLUGIN HELP MESSAGE GOES HERE")
@click.pass_context
def main(ctx):
    """Plugin entry."""
    return {{class_name}}()


if __name__ == '__main__':
    main()
