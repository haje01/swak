{% extends "tmpl_base.py" %}

{% block class_body %}

    def prepare_for_stream(self, tag, es):
        """Prepare to modify an event stream.

        Args:
            tag (str): Event tag
            es (EventStream): Event stream
        """
        pass

    def modify(self, tag, utime, record):
        """Modify an event.

        Args:
            tag (str): Event tag
            utime (float): Event time stamp.
            record (dict): Event record

        Returns:
            If modified
                float: Modified time
                record: Modified record

            If removed
                None
        """
        raise NotImplementedError()
{% endblock %}
