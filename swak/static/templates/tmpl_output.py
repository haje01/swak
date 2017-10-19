{% extends "tmpl_base.py" %}

{% block import_body %}
from swak.formatter import Formatter, StdoutFormatter
from swak.buffer import Buffer, MemoryBuffer
{% endblock %}

{% block class_body %}
    def _write(self, bulk):
        """Write a bulk.

        Args:
            bulk (bytearray or list): If the chunk that passes the argument is
              a binary type, bulk is an array of bytes, otherwise it is a list
              of strings.
        """
        raise NotImplementedError()
{% endblock %}

{% block cmd_body %}
@click.group(chain=True, invoke_without_command=True,
             help="Output to {{class_name}} output.")
@click.pass_context
def main(ctx):
    """Plugin entry."""
    pass


@main.resultcallback()
def process_components(components):
    """Process sub-command components and build an Output.

    Args:
        components (list)

    Returns:
        {{class_name}}
    """
    _formatter = _buffer = None
    for com in components:
        if isinstance(com, Formatter):
            _formatter = com
        if isinstance(com, Buffer):
            _buffer = com
    return {{class_name}}(_formatter, _buffer)


# MODIFY FOLLOWING FORMATTER INIT CODE TO FIT YOUR OUTPUT PLUGIN
@main.command('f.stdout', help="Stdout formatter for this output.")
@click.option('-z', '--timezone', default=None, show_default=True,
              help="Timezone for format.")
def f_stdout(timezone):
    """Formatter entry."""
    return StdoutFormatter(timezone=timezone)


# MODIFY FOLLOWING BUFFER INIT CODE TO FIT YOUR OUTPUT PLUGIN
@main.command('b.memory', help="Memory buffer for this output.")
@click.option('-f', '--flush-interval', default=None, show_default=True,
              help="Flush interval.")
def b_memory(flush_interval):
    """Formatter entry."""
    return MemoryBuffer(None, False, flush_interval=flush_interval)
{% endblock %}
