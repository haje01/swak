{% extends "tmpl_base.py" %}

{% block class_body %}

    def __init__(self):
        """Init."""
        super(Input, self).__init__()

    def start(self):
        """Start plugin.

        This method is called when the task starts after processing the
        setting. Creation of resources such as files and threads to be used in
        the plug-in is created here.
        """
        super({{class_name}}, self).start()
        # Allocate resources if necessary.

    def stop(self):
        """Stop plugin.

        This method is called when the task is preparing to shutdown. You
        should do simple things that do not fail, such as setting a thread
        stop flag.

        """
        super({{class_name}}, self).stop()

    def shutdown(self):
        """Shutdown plugin.

        This method is called when the task is completely shutdown. Here you
        can close or remove any files, threads, etc. that you had created in
        ``start``.
        """
        super({{class_name}}, self).shutdown()
        # Release resources if necessary.


    def read_lines(self):
        """Read lines.

        Yields:
            str: A line
        """
        raise NotImplementedError()
{% endblock %}
