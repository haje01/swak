"""This module implements pluginpod."""

import logging

from swak.datarouter import DataRouter
from swak.plugin import create_plugin_by_name, Input, Output, ProxyInput


MAX_BUFFER_RECORD = 10
MAX_BUFFER_TIME = 1.0


class PluginPod(object):
    """Plugin pod class."""

    def __init__(self, def_output):
        """Init.

        Args:
            def_output (Output): Default output.
        """
        self.name = "unnamed"
        self.def_output = def_output
        router = DataRouter(def_output)
        self.router = router
        self.plugins = []
        self.type = None

    def register_plugin(self, tag, plugin, insert_first=False):
        """Register a plugin by data tag pattern.

        Args:
            tag: Tag pattern.
            plugin: Plugin to regiseter.
            insert_first (bool): Do not append, insert at first.
        """
        logging.info("register_plugin - pod name '{}' tag '{}' plugin '{}' "
                     "first '{}'".format(self.name, tag, plugin, insert_first))
        assert self.router is not None
        assert plugin not in self.plugins
        if insert_first:
            self.plugins.insert(0, plugin)
        else:
            self.plugins.append(plugin)
        self.router.add_rule(tag, plugin, insert_first)

    def init_from_commands(self, tag, cmds):
        """Init agent from plugin commands.

        Args:
            tag (str): data tag.
            cmds (list): Seperated plugin commands list.
            check_input (bool): Check for input commands.

        Returns:
            Input: Starting input plugin
        """
        logging.info("init_from_commands")
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
        logging.info("starting all plugins")
        for plugin in self.iter_plugins():
            plugin.start()

    def stop(self):
        """Stop plugins in the router."""
        logging.info("stopping all plugins")
        for plugin in self.iter_plugins():
            plugin.stop()

    def flush(self, flush_all=False):
        """Flush all output plugins.

        Args:
            flush_all (bool): Whether flush all or just one.
        """
        logging.debug("flushing all output plugins")
        for output in self.iter_outputs():
            output.flush(flush_all)

    def shutdown(self):
        """Shutdown plugins in the router."""
        logging.info("shutting down all output plugins")
        for plugin in self.iter_plugins():
            plugin.shutdown()

    # def all_output_finished(self):
    #     """Whether all output is stopped & flushed or not."""
    #     for output in self.iter_outputs():
    #         if output.started:
    #             return False
    #         buffer = output.buffer
    #         if buffer is not None and buffer.started:
    #             return False
    #         if not buffer.empty:
    #             return False
    #     return True

    def may_chunking(self):
        """Chunking for all outputs if needed."""
        for output in self.iter_outputs():
            output.may_chunking()

    def may_flushing(self, last_flush_interval=None):
        """Flushing for all outputs if needed."""
        logging.debug("may_flushing")
        for output in self.iter_outputs():
            output.may_flushing(last_flush_interval)

    def process(self, stop_event):
        """Read from input and emit through router for service.

        This funciont is for service agent.

        Args:
            stop_event (threading.Event): Stop event
        """
        self.start()
        logging.info("start processing")
        # Read input and emit to data router until input finished.
        for tag, ds in self.input.read(stop_event):
            # Tag is None when no data from receiving queue of ProxyInput in
            #  aggregated thread model.
            if not(tag is None or ds.empty()):
                self.router.emit_stream(tag, ds, stop_event)
            # Need to check for flushing even if there is no data
            self.may_flushing()
        logging.info("stop event received")
        self.stop()
        self.shutdown()

    def simple_process(self, input_pl):
        """Read from input and emit through router.

        This funciont is for test agent.

        Args:
            input_pl (swak.plugin.Input): Input plugin to read data.
        """
        ainput = input_pl if input_pl is not None else self.input
        for tag, ds in ainput.read(None):
            if not ds.empty():
                self.router.emit_stream(tag, ds)
                # Check forflushing only when there is data.
                self.may_flushing()

    # def process_one(self, input_pl=None):
    #     """Process one record.

    #     Args:
    #         input_pl (swak.plugin.Input): Input plugin for simple process.

    #     Todo: Test for bulk data & Optimization.

    #     Returns:
    #         bool: True if the input has been closed, False otherwise.
    #     """
    #     logging.debug("process_one")
    #     ainput = input_pl if input_pl is not None else self.input
    #     try:
    #         record = ainput.read_one()
    #         if record:
    #             logging.debug("has a record, emit to router.")
    #             utime = time.time()
    #             self.router.emit(ainput.tag, utime, record)
    #         return False
    #     except InputClosed:
    #         logging.info("input has been closed.")
    #         return True
    #     finally:
    #         # need to check flushing here.
    #         self.may_flushing()

    @property
    def input(self):
        """Return input plugin."""
        assert len(self.plugins) > 0
        first = self.plugins[0]
        assert isinstance(first, Input) or isinstance(first, ProxyInput)
        return first
