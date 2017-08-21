"""Event."""


class EventStream(object):
    """EventStream class."""

    def __init__(self):
        """init."""
        super(EventStream, self).__init__()


class OneEventStream(EventStream):
    """EventStream class."""

    def __init__(self, arg):
        """init."""
        super(OneEventStream, self).__init__()
        self.arg = arg


class ArrayEventStream(EventStream):
    """EventStream class."""

    def __init__(self, entries):
        """init."""
        super(ArrayEventStream, self).__init__()
        self.entries = entries


class MultiEventStream(EventStream):
    """MultiEventStream class."""

    def __init__(self, time_array=[], record_array=[]):
        """init."""
        super(MultiEventStream, self).__init__()
        self.time_array = time_array
        self.record_array = record_array
