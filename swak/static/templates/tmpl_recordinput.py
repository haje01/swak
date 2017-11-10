{% extends "tmpl_base.py" %}

{% block class_body %}
    def __init__(self):
        """Init."""
        super(RecordInput, self).__init__()

    def generate_record(self):
        """Generate records.

        This function can be written in synchronous or asynchronous manner. To
         make it work asynchronously, return an empty record immediately under
         blocking situations.

        Note: When operating synchronously, flushing with time interval does
         not work.

        Yields:
            dict: A record.
        """
        raise NotImplementedError()
{% endblock %}
