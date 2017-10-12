"""This module implements core functions."""

import re
import logging
import sys

from swak.event_router import EventRouter
from swak.plugin import Input, DummyOutput, import_plugins_package
from swak.const import TEST_STREAM_TAG
from swak.util import get_plugin_module_name


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
            raise ValueError("Illegal test commands: {}".format(cmds))
        cmd = args[0]
        if i == 0 and not cmd.startswith('i.'):
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
                raise ValueError("There is no plugin '{}'".format(plugin_name))
        else:
            mod = sys.modules[path]
            return mod.main(args=args, standalone_mode=False)


def build_test_event_router(cmds, _test=False):
    """Build an event router for test commands.

    Args:
        cmds (list): Seperated test commands list.
        _test (bool): Test mode

    Returns:
        Input: Starting input plugin
        EventRouter
    """
    input_plugin = None
    router = EventRouter(DummyOutput(echo=not _test))
    for i, cmd in enumerate(cmds):
        args = cmd[1:]
        pname = cmd[0]
        plugin = _create_plugin_by_name(pname, args)
        plugin.set_router(router)
        if isinstance(plugin, Input):
            plugin.set_tag(TEST_STREAM_TAG)

        if i == 0:
            assert isinstance(plugin, Input)
            input_plugin = plugin
        else:
            router.add_rule(TEST_STREAM_TAG, plugin)

    return input_plugin, router


def run_test_cmds(cmds, _test=False):
    """Execute test command.

    Args:
        cmds (list): Parsed command list
        _test (bool): Test mode

    Returns:
        EventRouter: To test result.
    """
    input_plugin, router = build_test_event_router(cmds, _test)
    input_plugin.read()
    router.shutdown()
    return router
