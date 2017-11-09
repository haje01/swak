{% extends "tmpl_base.py" %}

{% block import_body %}
from swak.formatter import Formatter, StdoutFormatter
from swak.buffer import Buffer
from swak.memorybuffer import MemoryBuffer, DEFAULT_CHUNK_MAX_RECORD,\
    DEFAULT_CHUNK_MAX_SIZE, DEFAULT_BUFFER_MAX_CHUNK
{% endblock %}

{% block class_body %}
    def _write(self, bulk):
        """Write a bulk to the output.

        NOTE: A bulk can have the following types:
        - str: When there is no buffer
        - bytearray: When there is a buffer of binary format
        - list: When there is a buffer of string format

        An output plugin must support various bulk types depending on the
         presence and supported formats of the buffer.

        Args:
            bulk
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
@click.option('-f', '--flush-interval', default=None, type=str,
              show_default=True, help="Flush interval.")
@click.option('-r', '--chunk-max-record', default=DEFAULT_CHUNK_MAX_RECORD,
              type=int, show_default=True, help="Maximum records per chunk.")
@click.option('-s', '--chunk-max-size', default=DEFAULT_CHUNK_MAX_SIZE,
              show_default=True, help="Maximum chunks per buffer.")
@click.option('-c', '--buffer-max-chunk', default=DEFAULT_BUFFER_MAX_CHUNK,
              show_default=True, help="Maximum chunks per buffer.")
def b_memory(flush_interval, chunk_max_record, chunk_max_size,
             buffer_max_chunk):
    """Formatter entry."""
    return MemoryBuffer(None, False, flush_interval=flush_interval,
                        buffer_max_chunk=buffer_max_chunk,
                        chunk_max_record=chunk_max_record)
{% endblock %}
