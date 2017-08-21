"""Event rounter."""

from swak.event import OneEventStream
from swak.match import MatchPattern, OrMatchPattern


class Rule(object):
    """Rule class."""

    def __init__(self, pattern, collector):
        """init.

        Args:
            pattern (str): Glob style patterns seperated by space.
            collector: Filter or Output or EventRouter
        """
        patterns = [MatchPattern().create(ptrn) for ptrn in pattern.split()]
        self.pattern = patterns[0] if len(patterns) == 0 else\
            OrMatchPattern(patterns)
        self.collector = collector

    def match(self, tag):
        """Check tag match.

        Args:
            tag (str): Target tag

        Returns:
            (SRE_Match): Returns match object if tag matches, None otherwise.
        """
        return self.pattern.match(tag)


class EventRouter(object):
    """EvnetRouter is responsible to route events to a collector.

    1. Receive an event at emit method
    2. Match the event's tag with tag patterns
    3. Forward the event to the corresponding Collector

    Collector is either of Output, Transform or other EventRouter.
    """

    def __init__(self, default_output):
        """init.

        Args:
            default_output (BaseOutput): Output plugin
        """
        super(EventRouter, self).__init__()
        self.rules = []
        self.match_cache = {}
        self.default_output = default_output

    def emit(self, tag, time, record):
        """Emit one event."""
        self.emit_stream(tag, OneEventStream(time, record))

    def emit_stream(self, tag, es):
        """Emit stream with tag."""
        col = self.match_collector(tag)
        col.emit_events(tag, es)

    def add_rule(self, pattern, collector):
        """Add new rule.

        Args:
            pattern (str): Multipl Glob pattern seperated by spaces.
            collector
        """
        rule = Rule(pattern, collector)
        self.rules.append(rule)

    def match_collector(self, tag):
        """Match collector by tag."""
        if tag in self.match_cache:
            col = self.find_collector(tag)
            self.match_cache[tag] = col
        else:
            col = self.match_cache[tag]
        return col

    def find_collector(self, tag):
        """Find collector by tag."""
        for rule in self.rules:
            if rule.match(tag):
                return rule
        return self.default_output
