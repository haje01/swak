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
        for plugin in self.iter_plugins():
            if isinstance(plugin, Output):
                plugin.flush()

    def shutdown(self):
        """Shutdown plugins in the router."""
        for plugin in self.iter_plugins():
            plugin.shutdown()


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

    def simple_process(self, input_pl):
        """Simple process for a given input & router."""
        self.start()
        while True:
            tag = input_pl.tag
            try:
                record = input_pl.read_one()
                if record:
                    utime = time.time()
                    self.router.emit(tag, utime, record)
                else:
                    # may have data later.
                    pass
            except NoMoreData:
                # input has been finished.
                break

        # stop & shutdown router for flushing output.
        self.stop()
        self.shutdown()


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

    def run_commands(self, cmds, _test=False):
        """Init agent from test commands and execute them.

        Args:
            cmds (str): Unparsed commands string.
            _test (bool): Test mode

        Returns:
            EventRouter: To test result.
        """
        cmds = TRunAgent._parse_and_validate_cmds(cmds)
        input_pl = self._init_from_commands(cmds, _test)

        self.simple_process(input_pl)


class ServiceAgent(BaseAgent):
    """Service Agent."""

    def build_threads(self):
        """Build thread for service."""
        pass
