"""This module implements service agent."""
import sys
import threading

from swak.core import BaseAgent
from swak.exception import ConfigError
from swak.config import validate_cfg


class InputThread(threading.Thread):
    """Input thread class."""


class OutputThread(threading.Thread):
    """Output thread class."""


class ServiceAgent(BaseAgent):
    """Service Agent."""

    def __init__(self):
        """Init."""
        super(ServiceAgent, self).__init__(False)
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
        """Init thread for service.

        Args:
            cfg (dict): dict by parsing config text.
            dryrun (bool): Dry run(testing config) mode or not.
        """
        validate_cfg(cfg)
        if dryrun:
            return

        for tag, inputs in cfg['sources'].items():
            for inp in inputs:
                trd = InputThread()
                self.input_threads.append(trd)

        for tag, outputs in cfg['matches'].items():
            for out in outputs:
                trd = OutputThread()
                self.output_threads.append(trd)
