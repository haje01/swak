"""This module implements core functions."""

import sys
import time

from swak.event_router import EventRouter
from swak.plugin import Input, DummyOutput, import_plugins_package, Output
from swak.const import TESTRUN_TAG
from swak.util import get_plugin_module_name
from swak.exception import NoMoreData


class BaseAgent(object):
    """Agent class."""

    def __init__(self, test):
        """Init.

        Args:
            test: Test mode.
        """
        self.def_output = DummyOutput(echo=test)
        router = EventRouter(self.def_output)
        self.router = router
        self.plugins = []

    def register_plugin(self, tag, plugin):
        """Register a plugin by event tag pattern.

        Args:
            tag: A tag pattern.
            plugin: A plugin to regiseter.
        """
        assert self.router is not None
        assert plugin not in self.plugins
        self.plugins.append(plugin)
        self.router.add_rule(tag, plugin)

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

    def iter_outputs(self):
        """Iterate all output."""
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


class DummyAgent(BaseAgent):
    """Dummy agent for test."""

    def __init__(self):
        """Init."""
        super(DummyAgent, self).__init__(True)

    def emit(self, tag, time, record):
        """Emit by delegating to router."""
        self.router.emit(tag, time, record)

    def flush(self):
        """Delegate to router to be flushed."""
        for plugin in self.iter_plugins():
            if isinstance(plugin, Output):
                plugin.flush()

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

    @staticmethod
    def _parse_and_validate_cmds(cmds):
        """Parse and validate test commands.

        Vadation rule:
        - Starts with input plugin.
        - Zero or more modifier plugins.
        - Optionally finished with output plugin.

        Args:
            cmds (str): Unix shell command style test command.

        Yields:
            str: Each command string.
        """
        for i, cmd in enumerate(cmds.split('|')):
            args = [arg.strip() for arg in cmd.split()]
            if len(args) == 0:
                raise ValueError("Illegal test commands: {}".format(cmds))
            cmd = args[0]
            if i == 0 and not cmd.startswith('i.'):
                raise ValueError("Test command must starts with input plugin.")
            yield args

    @staticmethod
    def _create_plugin_by_name(plugin_name, args):
        """Create plugin by name for test command.

        Args:
            plugin_name (str): Plugin full name
            args (list): Command arguments to instantiate plugin object.

        Returns:
            Plugin module
        """
        for i in range(2):
            import_plugins_package(i == 0)
            try:
                elms = plugin_name.split('.')
                package_name = '.'.join(elms[1:])
                module_name = get_plugin_module_name(plugin_name)
                tn = 'std' if i == 0 else ''
                path = '{}plugins.{}.{}'.format(tn, package_name, module_name)
                __import__(path)
            except ImportError:
                if i == 0:
                    pass  # for external plugins
                else:
                    raise ValueError("There is no plugin '{}'".
                                     format(plugin_name))
            else:
                mod = sys.modules[path]
                return mod.main(args=args, standalone_mode=False)

    def _init_from_commands(self, cmds, test):
        """Init agent from test commands.

        Args:
            cmds (list): Seperated test commands list.
            _test (bool): Test mode

        Returns:
            Input: Starting input plugin
        """
        input_pl = None
        assert getattr(cmds, '__iter__') is not None
        for i, cmd in enumerate(cmds):
            args = cmd[1:]
            pname = cmd[0]
            plugin = TRunAgent._create_plugin_by_name(pname, args)
            self.register_plugin(TESTRUN_TAG, plugin)
            if i == 0:
                assert isinstance(plugin, Input)
                input_pl = plugin
        return input_pl

    def run_commands(self, cmds, last_flush_interval, _test=False):
        """Init agent from test commands and execute them.

        Args:
            cmds (str): Unparsed commands string.
            last_flush_interval (float): Force flushing interval for input
              is terminated.
            _test (bool): Test mode

        Returns:
            EventRouter: To test result.
        """
        cmds = TRunAgent._parse_and_validate_cmds(cmds)
        input_pl = self._init_from_commands(cmds, _test)

        self.simple_process(input_pl, last_flush_interval)


class ServiceAgent(BaseAgent):
    """Service Agent."""

    def build_threads(self):
        """Build thread for service."""
        pass
