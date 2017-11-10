{% extends "tmpl_base.py" %}

{% block class_body %}
    def __init__(self):
        """Init."""
        super(TextInput, self).__init__()

    def generate_line(self):
        """Generate text lines.

        This function can be written in synchronous or asynchronous manner. To
         make it work asynchronously, return an empty record immediately under
         blocking situations.

        Note: When operating synchronously, flushing with time interval does
         not work.

        Yields:
            str: A text line.
        """
        raise NotImplementedError()
{% endblock %}
