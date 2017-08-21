"""Core.

*****
:mod:`core`
*****
"""


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


def build_pipeline(cmds):
    """Build pipeline form commands list.

    Args:
        cmds (list): commands in string list

    Returns:
        (Pipeline): a Pipeline object
    """
    import swak.plugins  # protect dependency
    mmap = swak.plugins.MODULE_MAP

    # build  test pipeline
    pline = Pipeline()
    for cmd in cmds:
        args = cmd[1:]
        pname = cmd[0]
        pmod = mmap[pname]
        pline.append(pmod, args)
    return pline


def run_test_cmds(cmds):
    """Execute test command.

    Args:
        cmds (list): Parsed command list
    """
    pline = build_pipeline(cmds)
    pline.validate()
    pass
