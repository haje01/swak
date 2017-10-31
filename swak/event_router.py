"""This module implements event router."""
import logging

from swak.event import OneEventStream, MultiEventStream
from swak.match import MatchPattern, OrMatchPattern
from swak.plugin import Modifier, Output
from swak.config import select_and_parse

_, cfg = select_and_parse()
DEBUG = cfg['debug']
default_placeholder = None


class Pipeline(object):
    """Pipeline class."""

    def __init__(self, tag):
        """Init.

        Args:
            tag (str): Pipeline tag
        """
        self.modifiers = []
        self.output = None
        self.tag = tag

    def add_modifier(self, modifier):
        """Add modifier."""
        logging.debug("add_modifier {}".format(modifier))
        self.modifiers.append(modifier)

    def set_output(self, output):
        """Set output."""
        logging.debug("set_output {}".format(output))
        self.output = output

    def emit_events(self, tag, es):
        """Emit event to tagged stream.

        Optimize event stream by filters before emit.

        Args:
            tag (str): Event tag
            es (EventStream): Event stream to emit

        Returns:
            int: Adding size of the stream.
        """
        modified = self.modify_stream(tag, es)
        return self.output.emit_events(tag, modified)

    def modify_stream(self, tag, es):
        """Modify event stream.

        Args:
            es (EventStream): Event stream to be modified.

        Returns:
            If modified
                Modified MultiEventStream object

            If no modifiers exists
                Original event stream object
        """
        if len(self.modifiers) == 0:
            return es

        # give modifiers chance to do stream specific operation
        for mod in self.modifiers:
            mod.prepare_for_stream(tag, es)

        # modify each records
        times = []
        records = []
        for utime, record in es:
            skip = False
            for mod in self.modifiers:
                result = mod.modify(tag, utime, record)
                if result is None:
                    skip = True
                    break
                utime, record = result
            if not skip:
                times.append(utime)
                records.append(record)
        return MultiEventStream(times, records)


class Rule(object):
    """Rule class."""

    def __init__(self, pattern, collector):
        """init.

        Args:
            pattern (str): Glob style patterns seperated by space.
            collector: Modifier or Output
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


class Thread(object):
    """Thread class for plugins."""

    def __init__(self):
        """Init."""
        super(Thread, self).__init__()


class EventRouter(object):
    """EvnetRouter is responsible to route events to a collector.

    1. Receive an event at emit method
    2. Match the event's tag with tag patterns
    3. Forward the event to the corresponding Collector

    Collector is either of Output, Modifier.
    """

    def __init__(self, def_output):
        """init.

        Args:
            def_output (Output): Default output plugin
        """
        super(EventRouter, self).__init__()
        self.rules = []
        self.match_cache = {}
        assert isinstance(def_output, Output)
        self.def_output = def_output

    def emit(self, tag, utime, record):
        """Emit one event.

        Args:
            tag (str): Event tag.
            utime (float): Emit time stamp.
            record (dict): A record.

        Returns:
            int: Adding size of the stream if succeeded, or None.
        """
        return self.emit_stream(tag, OneEventStream(utime, record))

    def emit_stream(self, tag, es):
        """Emit stream with tag.

        Args:
            tag (str): Event tag
            es (EventStream): Event stream

        Returns:
            int: Adding size of the stream if succeeded, or None.
        """
        try:
            adding_size = self.match(tag).emit_events(tag, es)
            return adding_size
        except Exception as e:
            if DEBUG:
                raise
            logging.error(e)

    def add_rule(self, tag, collector):
        """Add new rule.

        Args:
            tag (str): Multiple patterns seperated by space for tag.
            collector (Plugin): Input or Modifier or Output plugin
        """
        logging.info("add_rule tag '{}' collector {}".format(tag, collector))
        collector.set_tag(tag)
        rule = Rule(tag, collector)
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
        logging.info("build_pipeline for tag '{}'".format(tag))
        pipeline = Pipeline(tag)
        for rule in self.rules:
            if not rule.match(tag):
                continue
            logging.debug("rule {}".format(rule))
            if isinstance(rule.collector, Modifier):
                pipeline.add_modifier(rule.collector)
            elif isinstance(rule.collector, Output):
                pipeline.set_output(rule.collector)
                return pipeline

        pipeline.set_output(self.def_output)
        return pipeline
