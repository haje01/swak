"""Swak core.
"""
import swak.plugins
from swak.pipeline import Pipeline


def parse_test_cmds(cmd):
    """Parseing test commands.

    Args:
        cmd (str): Unix shell command style test command.

    Yields:
        (str): Each command string.
    """
    for cmd in cmd.split('|'):
        args = [arg.strip() for arg in cmd.split()]
        if len(args) == 0:
            raise ValueError("Illegal test commands")
        yield args


def run_test_cmds(cmds):
    """Execute test command.

    Args:
        cmds (list): Parsed command list
    """
    mmap = swak.plugins.MODULE_MAP

    # build  test pipeline
    pline = Pipeline()
    for cmd in cmds:
        args = cmd[1:]
        pname = cmd[0]
        pmod = mmap[pname]
        pline.append(pmod, args)

    pline.validate()


def parse_and_run_test_cmds(cmds):
    """Parse test commands and execute them.

    Args:
        cmds (str): Commands string
    """
    for tcmd in parse_test_cmds(cmds):
        execute_test_cmd(tcmd)
