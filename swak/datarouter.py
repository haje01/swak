"""This module implements data router."""
import logging

from swak.data import MultiDataStream, OneDataStream
from swak.match import MatchPattern, OrMatchPattern
from swak.plugin import Modifier, Output, is_kind_of_output
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

    def emit_stream(self, tag, ds, stop_event):
        """Emit data stream output.

        Modify data and emit them.

        Args:
            tag (str): Data tag.
            ds (DataStream): Data stream to emit.
            stop_event (threading.Event): Stop event.

        Returns:
            int: Adding size of the stream.
        """
        logging.debug("emit_stream")
        modified = self.modify_stream(tag, ds)
        return self.output.emit_stream(tag, modified, stop_event)

    def modify_stream(self, tag, ds):
        """Modify data stream.

        Args:
            ds (DataStream): data stream to be modified.

        Returns:
            If modified
                Modified MultiDataStream object

            If no modifiers exists
                Original data stream object
        """
        if len(self.modifiers) == 0:
            return ds

        # Give modifiers chance to do stream specific operation
        for mod in self.modifiers:
            mod.prepare_for_stream(tag, ds)

        # Modify each records
        logging.debug("modify_stream")
        times = []
        records = []
        for utime, record in ds:
            skip = False
            for mod in self.modifiers:
                logging.debug("apply modifier {}".format(mod))
                result = mod.modify(tag, utime, record)
                if result is None:
                    skip = True
                    break
                utime, record = result
            if not skip:
                times.append(utime)
                records.append(record)
        logging.debug("modified records {}".format(records))
        return MultiDataStream(times, records)


class Rule(object):
    """Rule class."""

    def __init__(self, pattern, collector):
        """init.

        Args:
            pattern (str): Glob style patterns seperated by space.
            collector: Modifier or Output
        """
        patterns = [MatchPattern().create(ptrn) for ptrn in pattern.split()]
        self.pattern = patterns[0] if len(patterns) == 1 else\
            OrMatchPattern(patterns)
        self.collector = collector

    def match(self, tag):
        """Check tag match.

        Args:
            tag (str): data tag

        Returns:
            (SRE_Match): Returns match object if tag matches, None otherwise.
        """
        return self.pattern.match(tag)

    def __repr__(self):
        """Canonical string representation."""
        return "<Rule pattern '{}' with collector '{}'>".format(self.pattern,
                                                                self.collector)


class Thread(object):
    """Thread class for plugins."""

    def __init__(self):
        """Init."""
        super(Thread, self).__init__()


class DataRouter(object):
    """EvnetRouter is responsible to route datas to a collector.

    1. Receive an data at emit method
    2. Match the data's tag with tag patterns
    3. Forward the data to the corresponding Collector

    Collector is either of Output, Modifier.
    """

    def __init__(self, def_output):
        """init.

        Args:
            def_output (Output): Default output plugin
        """
        super(DataRouter, self).__init__()
        self.rules = []
        self.match_cache = {}
        assert isinstance(def_output, Output)
        self.def_output = def_output

    def emit(self, tag, utime, record):
        """Emit one data.

        Args:
            tag (str): Data tag.
            utime (float): Data time stamp.
            record (dict): A record.

        Returns:
            int: Adding size of the stream if succeeded, or None.
        """
        return self.emit_stream(tag, OneDataStream(utime, record))

    def emit_stream(self, tag, ds, stop_event):
        """Emit an data stream with tag.

        Args:
            tag (str): Data tag
            ds (DataStream): Data stream
            stop_event (threading.Event): Stop event.

        Returns:
            int: Adding size of the stream if succeeded, or None.
        """
        logging.debug("emit_stream tag '{}' ds {}".format(tag, ds))
        try:
            adding_size = self.match(tag).emit_stream(tag, ds, stop_event)
            return adding_size
        except Exception as e:
            if DEBUG:
                raise
            logging.error(e)

    def add_rule(self, tag, collector, insert_first):
        """Add new rule.

        Args:
            tag (str): Multiple patterns seperated by space for tag.
            collector (Plugin): Input or Modifier or Output plugin
            insert_first (bool): Do not append, insert at first.
        """
        logging.info("add_rule tag '{}' collector {}".format(tag, collector))
        collector.set_tag(tag)
        rule = Rule(tag, collector)
        if insert_first:
            self.rules.insert(0, rule)
        else:
            self.rules.append(rule)

    def match(self, tag):
        """Match pipeline by tag.

        Args:
            tag (str): data tag

        Returns:
            ``Pipeline``
        """
        if tag not in self.match_cache:
            logging.debug("DataRouter.match - not found in cache '{}'".
                          format(tag))
            pline = self.build_pipeline(tag)
            self.match_cache[tag] = pline
        else:
            pline = self.match_cache[tag]
        return pline

    def build_pipeline(self, tag):
        """Build a pipeline for tag and returns it.

        Args:
            tag (str): data tag.

        Returns:
            ``Pipeline``
        """
        logging.info("build_pipeline for tag '{}'".format(tag))
        pipeline = Pipeline(tag)
        for rule in self.rules:
            if not rule.match(tag):
                continue
            logging.info("matched tag '{}' rule {}".format(tag, rule))
            if isinstance(rule.collector, Modifier):
                pipeline.add_modifier(rule.collector)
            elif is_kind_of_output(rule.collector):
                pipeline.set_output(rule.collector)
                return pipeline

        logging.info("no output. fallback to default output '{}'".
                     format(self.def_output))
        pipeline.set_output(self.def_output)
        return pipeline
