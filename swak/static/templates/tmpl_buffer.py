{% extends "tmpl_base.py" %}

{% block class_body %}
    def __init__(self, binary, chunk_max_record, chunk_max_size,
                 buffer_max_chunk, buffer_max_size, flush_interval,
                 time_slice_format, time_slice_wait):
        """Init.

        Args:
            binary (bool): Store data as binary or not. Defaults to True.
            chunk_max_record (int): Maximum records for flushing.
            chunk_max_size (int): Maximum chunk size for flushing.
            buffer_max_chunk (int): Maximum chunk of a buffer for flushing.
            buffer_max_size (int): Maximum buffer size for flushing.
            flush_interval (int): Flush interval in seconds.
            time_slice_format (str): Time slicing format in python datetime
                format.
            time_slice_wait (int): Flush interval in seconds.
        """
        super(Memory, self).__init__(binary, chunk_max_record, chunk_max_size,
                                     buffer_max_chunk, buffer_max_size,
                                     flush_interval, time_slice_format,
                                     time_slice_wait)
        # initialization codes here.

    def append(self, es):
        """Append event stream to buffer.

        Args:
            es (EventStream): Event stream.
        """
        raise NotImplemented()
{% endblock %}
