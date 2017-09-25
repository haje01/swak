{% extends "tmpl_base.py" %}

{% block class_body %}
    def append(self, es):
        """Append event stream to buffer.

        Args:
            es (EventStream): Event stream.
        """
        raise NotImplemented()
{% endblock %}
