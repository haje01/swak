{% extends "tmpl_base.py" %}

{% block class_body %}
    def __init__(self):
        """Init."""
        super(TextInput, self).__init__()

    def generate_line(self):
        """Generate text lines.

        Note: Don't do blocking operation. return an empty string in inadequate
            situations.

        Yields:
            str: A text line.
        """
        raise NotImplementedError()
{% endblock %}
