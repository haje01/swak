{% extends "tmpl_base.py" %}

{% block class_body %}
    def __init__(self):
        """Init."""
        super(RecordInput, self).__init__()

    def read_record(self):
        """Generate a record from the source.

        Throw NoMoreData exception if no more record available.

        Raises:
            NoMoreData: No more data to generate.

        Returns:
            dict: A record. Return empty dict if conditions do not
                match.
        """
        raise NotImplementedError()
{% endblock %}
