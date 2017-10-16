{% extends "tmpl_base.py" %}
from swak.exception import NoMoreData

{% block class_body %}
    def __init__(self):
        """Init."""
        super(TextInput, self).__init__()

    def read_line(self):
        """Generate a line from the source.

        Raises:
            NoMoreData: No more data to generate.

        Throw NoMoreData exception if no more record available.

        Returns:
            str: A line. Return empty string if conditions do not match.
        """
        raise NotImplementedError()
{% endblock %}
