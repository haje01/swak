"""Common classes & functions for test."""
from collections import defaultdict

from swak.plugin import BaseOutput


class DummyOutput(BaseOutput):
    """Output plugin for test."""

    def __init__(self):
        """init."""
        super(DummyOutput, self).__init__()
        self.events = defaultdict(list)

    def emit_events(self, tag, es):
        """Emit events."""
        for time, record in es:
            print("tag {}, time {}, record {}".format(tag, time, record))
        self.events[tag].append((time, record))

    def emit(self, tag, es):
        """Process event stream."""
        for time, record in es:
            self.events[tag].append((time, record))
