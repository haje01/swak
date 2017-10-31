"""This module implements service agent."""
import sys
import time
import logging
import logging.config
import threading
import multiprocessing
import json

from queue import Queue

from swak.core import BaseAgent, PluginPod
from swak.exception import ConfigError
from swak.stdplugins.stdout.o_stdout import Stdout
from swak.util import parse_and_validate_cmds
from swak.plugin import ProxyOutput, ProxyInput, Output, Input
from swak.config import main_logger_config, validate_cfg

# set_log_verbosity(0)


def init_router(cmd):
    """Init an event router from plugin commands.

    Args:
        cmd (str): Plugin command for this router.
    """
    pass


class BaseThread(threading.Thread):
    """BaseThread class."""

    def __init__(self, stop_event):
        """Init.

        Args:
            stop_event (threading.Event): Stop event.
        """
        super(BaseThread, self).__init__()
        self.stop_event = stop_event
        def_output = Stdout()
        self.pluginpod = PluginPod(def_output)

    def init_from_commands(self, tag, cmds, for_input):
        """Init agent from plugin commands.

        Args:
            tag (str): Event tag.
            cmds (list): Seperated plugin commands list.
            for_input (bool): Whether to init for input or output.

        Returns:
            Input: Starting input plugin
        """
        return self.pluginpod.init_from_commands(tag, cmds)

    @property
    def plugins(self):
        """Return pluginpod's plugins."""
        return self.pluginpod.plugins

    def register_plugin(self, tag, plugin, insert_first=False):
        """Register a plugin by event tag pattern.

        Args:
            tag: Tag pattern.
            plugin: Plugin to regiseter.
            insert_first (bool): Do not append, insert at first.
        """
        self.pluginpod.register_plugin(tag, plugin, insert_first)

    def run(self):
        """Thread main."""
        self.pluginpod.process(self.stop_event)
        time.sleep(1)


class InputThread(BaseThread):
    """Input thread class."""

    def init_from_commands(self, tag, cmds):
        """Init input thread from config commands.

        Args:
            tag (str): Event tag.
            cmds (list): Seperated plugin commands list.

        Returns:
            Queue: If no output plugin exists, create an inter-proxy queue and
                return it, None otherwise.
        """
        self.name = "Input-{}".format(tag)
        super(InputThread, self).init_from_commands(tag, cmds, True)
        # makes a ProxyOutput if there is no output plugin.
        assert len(self.plugins) > 0, "No plugins were created."
        last_plugin = self.plugins[-1]
        if not isinstance(last_plugin, Output):
            queue = Queue()
            proxy_output = ProxyOutput(queue)
            self.register_plugin(tag, proxy_output)
            return queue


class OutputThread(BaseThread):
    """Output thread class."""

    def init_from_commands(self, tag, cmds):
        """Init output thread from config commands.

        Args:
            tag (str): Event tag.
            cmds (list): Seperated plugin commands list.
        """
        self.name = "Output-{}".format(tag)
        super(OutputThread, self).init_from_commands(tag, cmds, False)
        # confirm no input plugin.
        assert len(self.plugins) > 0
        for plugin in self.plugins:
            assert not isinstance(plugin, Input)
        # makes a ProxyInput and insert as first plugin
        proxy_input = ProxyInput()
        self.register_plugin(tag, proxy_input, True)
        self.proxy_input = proxy_input

    def append_proxy_input_queue(self, queue):
        """Append inter-proxy queue."""
        assert self.proxy_input is not None, "No ProxyInput created."
        self.proxy_input.append_recv_queue(queue)


class ServiceAgent(BaseAgent):
    """Service Agent."""

    def __init__(self):
        """Init."""
        super(ServiceAgent, self).__init__()
        self.name = multiprocessing.current_process().name
        self.input_threads = []
        self.output_threads = []
        self.stop_event = None

    def init_from_cfg(self, cfg, dryrun):
        """Init agent from config.

        Args:
            cfg (dict): dict from parsing config text.
            dryrun (bool): Dry run(testing config) mode or not.

        Returns:
            bool: False if init failed. True otherwise
        """
        if cfg is None:
            sys.stderr.write("No content in config.\n")
            return False
        try:
            validate_cfg(cfg)
            # init logger
            cfg = main_logger_config(cfg)
            logging.config.dictConfig(cfg['logger'])
            logging.critical("Init service agent '{}'".format(self.name))
            logging.info("effective config: \n{}".
                         format(json.dumps(cfg, indent=1)))
            self.init_threads(cfg, dryrun)
            # more init code here..
        except ConfigError as e:
            sys.stderr.write("{}\n".format(e))
            return False
        return True

    def init_threads(self, cfg, dryrun):
        """Init threads for service agent from config.

        There are two kinds of thread:
        - Input thread: Reads the event from the input, process them, and
            passes them to the output thread via ProxyOutput.
        - Onput thread: Reads the events from input thread via ProxyInput,
            process them, and passes them to the real output.

        Args:
            cfg (dict): dict from parsing config text.
            dryrun (bool): Dry run(testing config) mode or not.
        """
        if dryrun:
            return

        def create_input_thread(tag, cmd, stop_event):
            """Create input thread.

            Args:
                tag (str): Event tag.
                cmd (str): A string command to construct a input thread.
                stop_event (threading.Event): Stop event.

            Returns:
                str: Event tag.
                Queue: Inter-proxy queue if no output exists. None otherwise.
            """
            trd = InputThread(stop_event)
            cmds = parse_and_validate_cmds(cmd, True)
            tag = ' '.join(cmds[-1][1:])
            queue = trd.init_from_commands(tag, cmds)
            self.input_threads.append(trd)
            return tag, queue

        def create_output_thread(tag, cmd, stop_event):
            """Create output thread.

            Args:
                tag (str): Event tag.
                cmd (str): A string command to construct a input thread.
                stop_event (threading.Event): Stop event.
            """
            trd = OutputThread(stop_event)
            cmds = parse_and_validate_cmds(cmd, False)
            trd.init_from_commands(tag, cmds)
            self.output_threads.append(trd)

        # def init_from_cfg(cfg, for_input):
        #     """Init thread from config.

        #     Args:
        #         cfg (list): List of config strings.
        #     """

        self.stop_event = threading.Event()

        # create output threads first.
        if 'matches' in cfg:
            for tag, cmd in cfg['matches'].items():
                create_output_thread(tag, cmd, self.stop_event)

        # then create input threads
        for strcmd in cfg['sources']:
            proxy_info = create_input_thread(None, strcmd, self.stop_event)
            # Link input & output threads if needed
            if proxy_info is not None:
                tag, queue = proxy_info
                self.link_output_thread_with_proxy(tag, queue)

    def link_output_thread_with_proxy(self, tag, queue):
        """Link input and output thread."""
        for otrd in self.output_threads:
            match = otrd.pluginpod.router.match(tag)
            if match is None:
                raise ConfigError("No matching output thread found for '{}'".
                                  format(tag))
            else:
                assert len(otrd.pluginpod.plugins) > 0
                first_plugin = otrd.pluginpod.plugins[0]
                assert isinstance(first_plugin, ProxyInput)
                first_plugin.append_recv_queue(tag, queue)

    def start(self):
        """Start service."""
        assert len(self.input_threads) + len(self.output_threads) > 0, \
            "There are no threads to start."
        # start output threads first.
        for otrd in self.output_threads:
            otrd.start()
        for itrd in self.input_threads:
            itrd.start()

    def stop(self):
        """Stop service."""
        # stop threads by stop event.
        self.stop_event.set()

    def shutdown(self):
        """Shutdown service."""
        pass


if __name__ == '__main__':
    import yaml
    cfgs = '''
sources:
    - i.counter | m.reform -w tag t1 | tag test1
    - i.counter | m.reform -w tag t2 | tag test2

matches:
    test*: o.stdout
    '''
    cfg = yaml.load(cfgs)
    agent = ServiceAgent()
    agent.init_from_cfg(cfg, False)
    agent.start()
    time.sleep(2)
    agent.stop()
    agent.shutdown()
