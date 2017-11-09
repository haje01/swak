"""This module implements service agent."""
import sys
import logging
import logging.config
import threading
import multiprocessing
import json
import time

from queue import Queue

from swak.core import BaseAgent
from swak.exception import ConfigError
from swak.stdplugins.stdout.o_stdout import Stdout
from swak.util import parse_and_validate_cmds
from swak.plugin import ProxyOutput, ProxyInput, Output, Input
from swak.config import main_logger_config, validate_cfg
from swak.pluginpod import PluginPod
from swak import __version__

# set_log_verbosity(0)


def init_router(cmd):
    """Init data router from plugin commands.

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
        def_output.buffer = None  # no buffer for default output
        self.pluginpod = PluginPod(def_output)

    def init_from_commands(self, tag, cmds, for_input):
        """Init agent from plugin commands.

        Args:
            tag (str): data tag.
            cmds (list): Seperated plugin commands list.
            for_input (bool): Whether to init for input or output.

        Returns:
            Input: Starting input plugin
        """
        logging.info("init_from_commands thread name {}".format(self.name))
        return self.pluginpod.init_from_commands(tag, cmds)

    @property
    def plugins(self):
        """Return pluginpod's plugins."""
        return self.pluginpod.plugins

    def register_plugin(self, tag, plugin, insert_first=False):
        """Register a plugin by data tag pattern.

        Args:
            tag: Tag pattern.
            plugin: Plugin to regiseter.
            insert_first (bool): Do not append, insert at first.
        """
        self.pluginpod.register_plugin(tag, plugin, insert_first)

    def run(self):
        """Thread main."""
        logging.info("starting thread name '{}'.".format(self.name))
        self.pluginpod.process(self.stop_event)
        logging.info("finished thread name '{}'.".format(self.name))


class InputThread(BaseThread):
    """Input thread class."""

    def init_from_commands(self, tag, cmds):
        """Init input thread from config commands.

        Args:
            tag (str): data tag.
            cmds (list): Seperated plugin commands list.

        Returns:
            Queue: If no output plugin exists, create an inter-proxy queue and
                return it, None otherwise.
        """
        self.pluginpod.type = 'input'
        self.pluginpod.name = self.name = "InTrd-{}".format(tag)
        super(InputThread, self).init_from_commands(tag, cmds, True)

        # Makes a ProxyOutput if there is no output plugin.
        assert len(self.plugins) > 0, "No plugins were created."
        last_plugin = self.plugins[-1]
        if not isinstance(last_plugin, Output):
            # use buffering for inter-thread queue
            self.pluginpod.buffering = True
            queue = Queue()
            proxy_output = ProxyOutput(queue)
            self.register_plugin(tag, proxy_output)
            return queue


class OutputThread(BaseThread):
    """Output thread class."""

    def init_from_commands(self, tag, cmds):
        """Init output thread from config commands.

        Args:
            tag (str): data tag.
            cmds (list): Seperated plugin commands list.
        """
        self.pluginpod.type = 'output'
        self.pluginpod.name = self.name = "OutTrd-{}".format(tag)
        super(OutputThread, self).init_from_commands(tag, cmds, False)

        # Confirm no input plugin.
        assert len(self.plugins) > 0
        for plugin in self.plugins:
            assert not isinstance(plugin, Input)
        # Makes a ProxyInput and insert as first plugin
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
            # Init logger
            cfg = main_logger_config(cfg)
            if 'logger' in cfg:
                lcfg = cfg['logger']
                if lcfg is not None:
                    logging.config.dictConfig(lcfg)
            logging.critical("========== Swak Version {} ==========".
                             format(__version__))
            logging.critical("init service agent for '{}'".format(self.name))
            logging.info("effective config: \n{}".
                         format(json.dumps(cfg, indent=1)))
            self.init_threads(cfg, dryrun)
            # More init code here..
        except ConfigError as e:
            logging.error(e)
            sys.stderr.write("{}\n".format(e))
            return False
        return True

    def init_threads(self, cfg, dryrun):
        """Init threads for service agent from config.

        There are two kinds of thread:
        - Input thread: Reads data from the input, process them, and
            passes them to the output thread via ProxyOutput.
        - Onput thread: Reads data from input thread via ProxyInput,
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
                tag (str): data tag.
                cmd (str): A string command to construct a input thread.
                stop_event (threading.Event): Stop event.

            Returns:
                str: data tag.
                Queue: Inter-proxy queue if no output exists. None otherwise.
            """
            logging.info("create_input_thread with cmd '{}'".format(cmd))
            trd = InputThread(stop_event)
            cmds = parse_and_validate_cmds(cmd, True)
            last_cmd = cmds[-1]
            if last_cmd[0] == 'tag':
                tag = ' '.join(last_cmd[1:])
            else:
                tag = '_notag_'

            queue = trd.init_from_commands(tag, cmds)
            self.input_threads.append(trd)
            return tag, queue

        def create_output_thread(tag, cmd, stop_event):
            """Create output thread.

            Args:
                tag (str): data tag.
                cmd (str): A string command to construct a input thread.
                stop_event (threading.Event): Stop event.
            """
            logging.info("create_output_thread with cmd '{}'".format(cmd))
            trd = OutputThread(stop_event)
            cmds = parse_and_validate_cmds(cmd, False)
            trd.init_from_commands(tag, cmds)
            self.output_threads.append(trd)

        self.stop_event = threading.Event()

        # Create output threads first.
        if 'matches' in cfg:
            for tag, cmd in cfg['matches'].items():
                create_output_thread(tag, cmd, self.stop_event)

        # Then create input threads
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
        logging.critical("starting service agent '{}'".format(self.name))
        assert len(self.input_threads) + len(self.output_threads) > 0, \
            "There are no threads to start."
        # Start output threads first.
        for otrd in self.output_threads:
            otrd.start()
        for itrd in self.input_threads:
            itrd.start()

    def stop(self):
        """Stop service."""
        # Stop threads by stop event.
        logging.critical("stopping service agent '{}'".format(self.name))
        self.stop_event.set()

    def shutdown(self):
        """Waiting for all threads to shut down."""
        for otrd in self.output_threads:
            otrd.join()
        for itrd in self.input_threads:
            itrd.join()

        # Other shutdown processes goes here.

        logging.critical("service agent has been successfully shut down for "
                         "'{}'".format(self.name))

if __name__ == '__main__':
    import yaml
    cfgs = '''
logger:
    root:
        level: CRITICAL

sources:
    - i.counter -n 100 | m.reform -w tag t1 | tag test1
    - i.counter -n 100 | m.reform -w tag t2 | tag test2
    - i.counter -n 100 | m.reform -w tag t3 | tag test3

matches:
    test*: o.stdout b.memory -f 1
    '''
    cfg = yaml.load(cfgs)
    agent = ServiceAgent()
    agent.init_from_cfg(cfg, False)
    agent.start()
    time.sleep(1)
    agent.stop()
    agent.shutdown()
