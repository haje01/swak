"""This module implements core functions."""

import time

from swak.event_router import EventRouter
from swak.plugin import Input, DummyOutput, Output, create_plugin_by_name
from swak.const import TESTRUN_TAG
from swak.exception import NoMoreData
from swak.util import parse_and_validate_cmds


class PluginPod(object):
    """Plugin pod class."""

    def __init__(self, def_output):
        """Init.

        Args:
            def_output (Output): Default output.
        """
        self.def_output = def_output
        router = EventRouter(def_output)
        self.router = router
        self.plugins = []

    def register_plugin(self, tag, plugin, insert_first=False):
        """Register a plugin by event tag pattern.

        Args:
            tag: Tag pattern.
            plugin: Plugin to regiseter.
            insert_first (bool): Do not append, insert at first.
        """
        assert self.router is not None
        assert plugin not in self.plugins
        if insert_first:
            self.plugins.insert(0, plugin)
        else:
            self.plugins.append(plugin)
        self.router.add_rule(tag, plugin)

    def init_from_commands(self, tag, cmds):
        """Init agent from plugin commands.

        Args:
            tag (str): Event tag.
            cmds (list): Seperated plugin commands list.
            check_input (bool): Check for input commands.

        Returns:
            Input: Starting input plugin
        """
        input_pl = None
        assert getattr(cmds, '__iter__') is not None
        last_idx = len(cmds) - 1
        for i, cmd in enumerate(cmds):
            args = cmd[1:]
            pname = cmd[0]
            if pname == 'tag':
                assert i == last_idx
                break
            plugin = create_plugin_by_name(pname, args)
            self.register_plugin(tag, plugin)
            if i == 0 and isinstance(plugin, Input):
                input_pl = plugin
        return input_pl

    def iter_plugins(self):
        """Iterate all plugins in the agent.

        Yield router's default output if no output is exists.
        """
        no_output = True
        for plugin in self.plugins:
            if isinstance(plugin, Output):
                no_output = False
            yield plugin
        if no_output:
            yield self.router.def_output

    def iter_inputs(self):
        """Iterate all inputs."""
        for plugin in self.iter_plugins():
            if isinstance(plugin, Input):
                yield plugin

    def iter_outputs(self):
        """Iterate all outputs."""
        for plugin in self.iter_plugins():
            if isinstance(plugin, Output):
                yield plugin

    def start(self):
        """Start plugins in the router."""
        for plugin in self.iter_plugins():
            plugin.start()

    def stop(self):
        """Stop plugins in the router."""
        for plugin in self.iter_plugins():
            plugin.stop()

    def flush(self):
        """Flush all output plugins."""
        for output in self.iter_outputs():
            output.flush()

    def shutdown(self):
        """Shutdown plugins in the router."""
        for plugin in self.iter_plugins():
            plugin.shutdown()

    def all_output_finished(self):
        """Whether all output is stopped & flushed or not."""
        for output in self.iter_outputs():
            if output.started:
                return False
            buffer = output.buffer
            if buffer is not None and buffer.started:
                return False
            if not buffer.empty:
                return False
        return True

    def may_chunking(self):
        """Chunking for all outputs if needed."""
        for output in self.iter_outputs():
            output.may_chunking()

    def may_flushing(self, last_flush_interval=None):
        """Flushing for all outputs if needed."""
        for output in self.iter_outputs():
            output.may_flushing(last_flush_interval)


class BaseAgent(object):
    """Agent class."""

    def __init__(self):
        """Init."""
        def_output = DummyOutput(echo=True)
        self.pluginpod = PluginPod(def_output)
        self.started = False

    def init_from_commands(self, tag, cmds):
        """Init agent from plugin commands.

        Args:
            tag (str): Event tag.
            cmds (list): Seperated plugin commands list.

        Returns:
            Input: Starting input plugin
        """
        assert type(tag) is str
        assert type(cmds) is list
        return self.pluginpod.init_from_commands(tag, cmds)

    def flush(self):
        """Flush all output pluginpod."""
        self.pluginpod.flush()

    def start(self):
        """Start plugins in the pluginpod."""
        assert not self.started
        self.pluginpod.start()
        self.started = True

    def stop(self):
        """Stop plugins in the pluginpod."""
        assert self.started
        self.pluginpod.stop()
        self.started = False

    def register_plugin(self, tag, plugin):
        """Register a plugin by event tag pattern.

        Args:
            tag: Tag pattern.
            plugin: Plugin to regiseter.
        """
        self.pluginpod.register_plugin(tag, plugin)

    def may_flushing(self, last_flush_interval=None):
        """Flushing for all outputs if needed."""
        self.pluginpod.may_flushing(last_flush_interval)

    def all_output_finished(self):
        """Whether all output is stopped & flushed or not."""
        return self.pluginpod.all_output_finished()

    def shutdown(self):
        """Shutdown plugins in the router."""
        self.pluginpod.shutdown()

    @property
    def plugins(self):
        """Return pluginpod's plugins."""
        return self.pluginpod.plugins

    @property
    def def_output(self):
        """Return pluginpod's default output."""
        return self.pluginpod.def_output

    @property
    def router(self):
        """Return pluginpod's event router."""
        return self.pluginpod.router

    def emit(self, tag, time, record):
        """Emit by delegating to router."""
        self.router.emit(tag, time, record)


class DummyAgent(BaseAgent):
    """Dummy agent for test."""

    def simple_process(self, input_pl, last_flush_interval):
        """Simple process for a given input & router."""
        self.start()
        # read input and emit to event router until input finished.
        while True:
            if self.simple_process_one(input_pl):
                break

        # input finished. stop and wait until all output flushed.
        self.stop()
        while not self.all_output_finished():
            self.may_flushing(last_flush_interval)
            time.sleep(0.1)

        # shutdown
        self.shutdown()

    def simple_process_one(self, input_pl):
        """Process one record.

        Args:
            input_pl: Input plugin to process.

        Returns:
            bool: True if the input has finished, False otherwise.
        """
        try:
            record = input_pl.read_one()
            if record:
                utime = time.time()
                self.router.emit(input_pl.tag, utime, record)
            return False
        except NoMoreData:
            return True
        finally:
            # need to check timely flushing here.
            self.may_flushing()


class TRunAgent(DummyAgent):
    """Test run agent class."""

    def run_commands(self, cmds, last_flush_interval):
        """Init agent from plugin commands and execute them.

        Args:
            cmds (str): Unparsed commands string.
            last_flush_interval (float): Force flushing interval for input
              is terminated.
            _test (bool): Test mode

        Returns:
            EventRouter: To test result.
        """
        cmds = parse_and_validate_cmds(cmds, True, False)
        input_pl = self.init_from_commands(TESTRUN_TAG, cmds)

        self.simple_process(input_pl, last_flush_interval)
