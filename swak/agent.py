"""This module implements service agent."""
import sys
import threading

from swak.core import BaseAgent, PluginPod
from swak.exception import ConfigError
from swak.config import validate_cfg
from swak.stdplugins.stdout.o_stdout import Stdout
from swak.util import parse_and_validate_cmds


def init_router(cmd):
    """Init an event router from plugin commands.

    Args:
        cmd (str): Plugin command for this router.
    """
    pass


class BaseThread(threading.Thread):
    """BaseThread class."""

    def __init__(self):
        """Init."""
        super(BaseThread, self).__init__()
        def_output = Stdout()
        self.pluginpod = PluginPod(def_output)

    def init_from_commands(self, tag, cmds, check_input):
        """Init agent from plugin commands.

        Args:
            tag (str): Event tag.
            cmds (list): Seperated plugin commands list.
            check_input (bool): Check command for input.

        Returns:
            Input: Starting input plugin
        """
        return self.pluginpod.init_from_commands(tag, cmds, check_input)


class InputThread(BaseThread):
    """Input thread class."""


class OutputThread(BaseThread):
    """Output thread class."""


class ServiceAgent(BaseAgent):
    """Service Agent."""

    def __init__(self):
        """Init."""
        super(ServiceAgent, self).__init__()
        self.input_threads = []
        self.output_threads = []

    def init_from_config(self, cfg, dryrun):
        """Init agent from config.

        Args:
            cfg (dict): dict by parsing config text.
            dryrun (bool): Dry run(testing config) mode or not.

        Returns:
            bool: False if init failed. True otherwise
        """
        if cfg is None:
            sys.stderr.write("No content in config.\n")
            return False

        try:
            self.init_threads(cfg, dryrun)
            # more init code here..
        except ConfigError as e:
            sys.stderr.write("{}\n".format(e))
            return False
        return True

    def init_threads(self, cfg, dryrun):
        """Init thread for service agent.

        Args:
            cfg (dict): dict by parsing config text.
            dryrun (bool): Dry run(testing config) mode or not.
        """
        validate_cfg(cfg)
        if dryrun:
            return

        def create_thread(tag, strcmd, for_input):
            cmds = parse_and_validate_cmds(strcmd, for_input,
                                           for_input)
            if for_input:
                tag = ' '.join(cmds[-1][1:])
            trd = InputThread() if for_input else OutputThread()
            trd.init_from_commands(tag, cmds, for_input)
            threads = self.input_threads if for_input else \
                self.output_threads
            threads.append(trd)

        def init_from_cfg(cfg, for_input):
            """Init thread from config.

            Args:
                cfg (list): List of config strings.
            """
            if for_input:
                for strcmd in cfg:
                    create_thread(None, strcmd, True)
            else:
                for tag, strcmd in cfg.items():
                    create_thread(tag, strcmd, False)

        init_from_cfg(cfg['sources'], True)
        init_from_cfg(cfg['matches'], False)
