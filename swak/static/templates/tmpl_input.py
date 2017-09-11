{% extends "tmpl_base.py" %}

{% block class_body %}

    def __init__(self):
        """Init."""
        super(Input, self).__init__()

    def generate_records(self):
        """Yield multiple records.

        Yields:
            dict: A record
        """
        raise NotImplementedError()


{% endblock %}
