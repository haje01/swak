"""Event rounter."""
import logging

from swak.event import OneEventStream, MultiEventStream
from swak.match import MatchPattern, OrMatchPattern
from swak.plugin import BaseReform
from swak.config import select_and_parse

_, cfg = select_and_parse()
DEBUG = cfg['debug']


class Pipeline(object):
    """Pipeline class."""

    def __init__(self):
        """Init."""
        self.reforms = []
        self.output = None

    def add_reform(self, reform):
        """Add reform."""
        self.reforms.append(reform)

    def set_output(self, output):
        """Set output."""
        self.output = output

    def emit_events(self, tag, es):
        """Emit event to tagged stream.

        Optimize event stream by filters before emit.

        Args:
            tag (str): Event tag
            es (EventStream): Event stream to emit
        """
        reformed = self.reform_stream(tag, es)
        self.output.emit_events(tag, reformed)

    def reform_stream(self, tag, es):
        """Reform event stream.

        Args:
            es (EventStream): Event stream to be reformed.

        Returns:
            If reformed
                Reformed MultiEventStream object

            If no reform exists
                Original event stream object
        """
        if len(self.reforms) == 0:
            return es

        times = []
        records = []
        for time, record in es:
            skip = False
            for ref in self.reforms:
                result = ref.reform(tag, time, record)
                if result is None:
                    skip = True
                    break
                time, record = result
            if not skip:
                times.append(time)
                records.append(record)
        return MultiEventStream(times, records)


class Rule(object):
    """Rule class."""

    def __init__(self, pattern, collector):
        """init.

        Args:
            pattern (str): Glob style patterns seperated by space.
            collector: Reform or Output
        """
        patterns = [MatchPattern().create(ptrn) for ptrn in pattern.split()]
        self.pattern = patterns[0] if len(patterns) == 0 else\
            OrMatchPattern(patterns)
        self.collector = collector

    def match(self, tag):
        """Check tag match.

        Args:
            tag (str): Event tag

        Returns:
            (SRE_Match): Returns match object if tag matches, None otherwise.
        """
        return self.pattern.match(tag)

    def emit_events(self, es):
        """Emit event stream.

        Args:
            es (EventStream): Event stream to emit.
        """
        self.collector


class EventRouter(object):
    """EvnetRouter is responsible to route events to a collector.

    1. Receive an event at emit method
    2. Match the event's tag with tag patterns
    3. Forward the event to the corresponding Collector

    Collector is either of Output, Reform.
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
        """Emit one event.

        Args:
            tag (str): Event tag
            time (float): Emit time
            record (dict): A record.
        """
        self.emit_stream(tag, OneEventStream(time, record))

    def emit_stream(self, tag, es):
        """Emit stream with tag.

        Args:
            tag (str): Event tag
            es (EventStream): Event stream

        Returns:
            bool: True if emit succeeds, False otherwise.
        """
        try:
            self.match(tag).emit_events(tag, es)
            return True
        except Exception as e:
            if DEBUG:
                raise
            logging.error(e)
            return False

    def add_rule(self, pattern, collector):
        """Add new rule.

        Args:
            pattern (str): Multiple Glob pattern seperated by space.
            collector
        """
        rule = Rule(pattern, collector)
        self.rules.append(rule)

    def match(self, tag):
        """Match pipeline by tag.

        Args:
            tag (str): Event tag

        Returns:
            ``Pipeline``
        """
        if tag not in self.match_cache:
            pline = self.build_pipeline(tag)
            self.match_cache[tag] = pline
        else:
            pline = self.match_cache[tag]
        return pline

    def build_pipeline(self, tag):
        """Build a pipeline for tag and returns it.

        Args:
            tag (str): Event tag.

        Returns:
            ``Pipeline``
        """
        pipeline = Pipeline()
        for rule in self.rules:
            if not rule.match(tag):
                continue
            if isinstance(rule.collector, BaseReform):
                pipeline.add_reform(rule.collector)
            else:
                pipeline.set_output(rule.collector)
                return pipeline

        pipeline.set_output(self.default_output)
        return pipeline
