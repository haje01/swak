"""This module implements core functions."""

from six import string_types

from swak.plugin import DummyOutput
from swak.util import parse_and_validate_cmds
from swak.const import TESTRUN_TAG
from swak.pluginpod import PluginPod


class BaseAgent(object):
    """Agent class."""

    def __init__(self):
        """Init."""
        def_output = DummyOutput(echo=True)
        self.pluginpod = PluginPod(def_output)
        self.pluginpod.type = 'agent'
        self.started = False

    def init_from_commands(self, tag, cmds):
        """Init agent from plugin commands.

        Args:
            tag (str): data tag.
            cmds (list): Seperated plugin commands list.

        Returns:
            Input: Starting input plugin
        """
        assert isinstance(tag, string_types)
        assert type(cmds) is list
        return self.pluginpod.init_from_commands(tag, cmds)

    def flush(self):
        """Flush all output pluginpod."""
        raise NotImplementedError()

    def start(self):
        """Start plugins in the pluginpod."""
        raise NotImplementedError()

    def stop(self):
        """Stop plugins in the pluginpod."""
        raise NotImplementedError()

    def may_flushing(self):
        """Flushing for all outputs if needed."""
        raise NotImplementedError()

    # def all_output_finished(self):
    #     """Whether all output is stopped & flushed or not."""
    #     raise NotImplementedError()

    def shutdown(self):
        """Shutdown plugins in the router."""
        raise NotImplementedError()


class DummyAgent(BaseAgent):
    """Dummy agent class for test."""

    def flush(self, flush_all=False):
        """Flush all output pluginpod.

        Args:
            flush_all (bool): Whether flush all or just one.
        """
        self.pluginpod.flush(flush_all)

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
        """Register a plugin by data tag pattern.

        Args:
            tag: Tag pattern.
            plugin: Plugin to regiseter.
        """
        self.pluginpod.register_plugin(tag, plugin)

    def may_flushing(self):
        """Flushing for all outputs if needed."""
        self.pluginpod.may_flushing()

    # def all_output_finished(self):
    #     """Whether all output is stopped & flushed or not."""
    #     return self.pluginpod.all_output_finished()

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
        """Return pluginpod's data router."""
        return self.pluginpod.router

    def emit(self, tag, time, record):
        """Emit by delegating to router."""
        self.router.emit(tag, time, record)

    def simple_process(self, input_pl):
        """Simple process for a given input & router.

        Args:
            input_pl (swak.plugin.Input): Input plugin to read event.
            last_flush_interval (float): Force flushing interval when input
              is terminated.
        """
        self.pluginpod.simple_process(input_pl)


class TRunAgent(DummyAgent):
    """Test run agent class."""

    def run_commands(self, cmds):
        """Init agent from plugin commands and execute them.

        Args:
            cmds (str): Unparsed commands string.

        Returns:
            DataRouter: To test result.
        """
        cmds = parse_and_validate_cmds(cmds, True, False)
        input_pl = self.pluginpod.init_from_commands(TESTRUN_TAG, cmds)
        self.start()
        self.simple_process(input_pl)
        self.stop()
        self.shutdown()
