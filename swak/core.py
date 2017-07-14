"""Swak core.
"""
import swak.plugins


def parse_test_cmds(cmd):
    """Parseing test commands.

    Args:
        cmd (str): Unix shell command style test command.

    Yields:
        (str): Each command string.
    """
    for cmd in cmd.split('|'):
        args = cmd.split()
        assert len(args) > 0
        yield args



def run_test_cmds(cmds):
    """Execute test command.

    Args:
        cmds (list): Parsed command list
    """
    for cmd in cmds:
        pass


def parse_and_run_test_cmds(cmds):
    """Parse test commands and execute them.

    Args:
        cmds (str): Commands string
    """
    for tcmd in parse_test_cmds(cmds):
        execute_test_cmd(tcmd)
