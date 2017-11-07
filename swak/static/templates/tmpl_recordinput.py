{% extends "tmpl_base.py" %}

{% block class_body %}
    def __init__(self):
        """Init."""
        super(RecordInput, self).__init__()

    def generate_record(self):
        """Generate records.

        Note: Don't do blocking operation. return an empty dict in inadequate
            situations.

        Yields:
            dict: A record.
        """
        raise NotImplementedError()
{% endblock %}
