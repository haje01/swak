{% extends "tmpl_base.py" %}

{% block class_body %}

    def __init__(self):
        """Init."""
        super(BaseInput, self).__init__()
        self.filter_fn = None

    def read(self):
        """Read data from source.

        It is implemented in the following format.

        1. Read the line-delimited text from the source.
        2. If the ``encoding`` is specified, convert it to ``utf8`` text.
        3. Separate text by new line,
        4. Filter lines if filter function exists.
        5. Yield them. If this is an input plugin for data of a known type,
           such as ``syslog``, it shall parse itself and return the record,
           otherwise it will just return the line.

        """
        raise NotImplemented()


{% endblock %}
