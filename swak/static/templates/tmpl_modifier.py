{% extends "tmpl_base.py" %}

{% block class_body %}

    def prepare_for_stream(self, tag, ds):
        """Prepare to modify data stream.

        Args:
            tag (str): data tag
            ds (datatream): data stream
        """
        pass

    def modify(self, tag, utime, record):
        """Modify data.

        Args:
            tag (str): data tag
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
