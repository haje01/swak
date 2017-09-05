{% extends "tmpl_base.py" %}

{% block class_body %}

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

{% endblock %}
