"""This module implements core functions."""

import re
import logging
import time

from swak.plugin import BaseInput
from swak.event_router import EventRouter
from swak.plugin import DummyOutput
from swak.const import TEST_STREAM_TAG


cmd_ptrn = re.compile(r'\S*(?P<cmd>((in\.|par\.|mod\.|buf\.|out\.|cmd\.)\S+)'
                      r'(\s+[^|$]+)?)')


def parse_and_validate_test_cmds(cmds):
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
            raise ValueError("Illegal test commands")
        cmd = args[0]
        if i == 0 and not cmd.startswith('in.'):
            raise ValueError("Test command must starts with input plugin.")
        yield args


def _parse_test_cmds(cmds):
    while cmds:
        match = cmd_ptrn.search(cmds)
        if match:
            cmd = match.group().strip()
            yield cmd
            endpos = match.span()[1]
            cmds = cmds[endpos + 1:]
        else:
            logging.error("Irregular command: '{}'".format(cmds))


def _create_plugin_from_cmd(cmd, args):
    """Create plugin from command.

    Args:
        cmd (str): Command name.
        args (list): Command arguments list

    Returns:
        Plugin module
    """
    import swak.stdplugins  # prevent dependency
    mmap = swak.stdplugins.MODULE_MAP
    for pname in mmap.keys():
        if pname == cmd:
            plugin = mmap[cmd].main(args=args, standalone_mode=False)
            return plugin

    import swak.plugins  # prevent dependency
    mmap = swak.plugins.MODULE_MAP
    for pname in mmap.keys():
        if pname == cmd:
            plugin = mmap[cmd].main(args=args, standalone_mode=False)
            return plugin


def build_test_event_router(cmds, _test=False):
    """Build event router for test commands.

    Args:
        cmds (list): Seperated test commands list.
        _test (bool): Test mode

    Returns:
        BaseInput: Starting input plugin
        EventRouter
    """
    input_plugin = None
    router = EventRouter(DummyOutput(echo=not _test))
    for i, cmd in enumerate(cmds):
        args = cmd[1:]
        cmd = cmd[0]
        plugin = _create_plugin_from_cmd(cmd, args)
        if i == 0:
            assert isinstance(plugin, BaseInput)
            input_plugin = plugin
        else:
            router.add_rule(TEST_STREAM_TAG, plugin)

    return input_plugin, router


def run_test_cmds(cmds, _test=False):
    """Execute test command.

    Args:
        cmds (list): Parsed command list
        _test (bool): Test mode

    Return:
        EventRouter: To test result.
    """
    input_plugin, router = build_test_event_router(cmds, _test)
    # pline.validate()
    for data in input_plugin.read():
        t = time.time()
        if type(data) is str:
            # text
            raise NotImplemented()
        else:
            # record
            router.emit(TEST_STREAM_TAG, t, data)

    return router
