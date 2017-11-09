"""This module implements utility functions."""

import os
import sys
import re
from platform import platform
import collections
import errno
import logging

from swak.exception import UnsupportedPython, ConfigError

test_logger_inited = False

LOG_FMT = logging.Formatter('%(levelname)s [%(filename)s:%(lineno)d]'
                            ' %(message)s')

size_ptrn_k = re.compile('(\d+)k', re.I)
size_ptrn_m = re.compile('(\d+)m', re.I)
size_ptrn_g = re.compile('(\d+)g', re.I)
size_ptrn_t = re.compile('(\d+)t', re.I)

time_ptrn_s = re.compile('(\d+)s', re.I)
time_ptrn_m = re.compile('(\d+)m', re.I)
time_ptrn_h = re.compile('(\d+)h', re.I)
time_ptrn_d = re.compile('(\d+)d', re.I)


def query_stream_log_handler(logger):
    """Query stream handler from logger."""
    if len(logger.handlers):
        ch = logger.handlers[0]
    else:
        ch = logging.StreamHandler()
        logger.addHandler(ch)
    return ch


def make_dirs(adir):
    """Make directory if not exist.

    Args:
        adir (str): A directory to create.
    """
    try:
        os.makedirs(adir)
    except OSError as err:
        if err.errno != errno.EEXIST:
            raise
        else:
            # directory already exists
            pass


def is_windows():
    """Return where windows or not.

    Returns:
        (bool): True if the OS is Windows or False.
    """
    plt = platform()
    return 'Windows' in plt


def get_winsvc_status(svcname):
    """Get Windows service status.

    Args:
        svcname (str): Service name to query.

    Returns:
        (str): Service Status string.
    """
    import win32serviceutil
    import pywintypes

    try:
        ret = win32serviceutil.QueryServiceStatus(svcname)
    except pywintypes.error:
        return None
    return ret


def update_dict(d, u):
    """Update dictionary recursively.

    Update dictionary ``d`` with the value of ``u`` of matching key &
        hierarchy.

    Args:
        d (dict): Original dictionary to be updated.
        u (dict): Referential dictionary

    Returns:
        dict: Update dictionary ``d``

    """
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            r = update_dict(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d


def init_home(home, cfg):
    """Initialized required directories for home.

    Check following paths and make directories if needed.
        - run/
        - log/ (in view of logger/handlers/file/filename of config)
    """
    make_dirs(os.path.join(home, 'run'))
    make_dirs(os.path.join(home, 'logs'))
    if 'logger' in cfg:
        logger = cfg['logger']
        if 'handlers' in logger:
            handlers = logger['handlers']
            if 'file' in handlers:
                file = handlers['file']
                if 'filename' in file:
                    fname = file['filename']
                    dname = os.path.dirname(fname)
                    make_dirs(dname)


def test_logconfig():
    """Config logger for test."""
    global test_logger_inited

    if test_logger_inited:
        return
    test_logger_inited = True

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = query_stream_log_handler(logger)
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(LOG_FMT)


def check_python_version():
    """Check python version and return version info.

    Returns:
        int: 2 if Python version is 2.x
             3 if >= 3.5
             else raises.

    Raises:
        UnsupportedPython: If current python version is not supported.
    """
    vi = sys.version_info
    major, minor = vi[0:2]
    if major == 2:
        return 2
    if major == 3 and minor >= 5:
        return 3
    else:
        raise UnsupportedPython("Python {} is not supported".format(vi))


def get_plugin_module_name(plugin_name):
    """Get plugin module name from plugin full name.

    Args:
        plugin_name (str): plugin full name

    Returns:
        str: Plugin module name
    """
    elm = plugin_name.split('.')
    assert len(elm) > 1
    return '{}_{}'.format(elm[0], '.'.join(elm[1:]))


def which_exe(program):
    """Find executable location."""
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def size_value(sval):
    """Convert suffixed size string to a value.

    k = kilo bytes
    m = mega bytes
    g = giga bytes
    t = tera bytes

    Args:
        sval (str): Size expression with suffix

    Returns:
        int: Bytes

    Raises:
        ConfigError: If conversion failed.
    """
    if sval is None:
        return None

    match = size_ptrn_k.match(sval)
    if match is not None:
        return int(match.groups()[0]) * 1024
    match = size_ptrn_m.match(sval)
    if match is not None:
        return int(match.groups()[0]) * (1024 ** 2)
    match = size_ptrn_g.match(sval)
    if match is not None:
        return int(match.groups()[0]) * (1024 ** 3)
    match = size_ptrn_t.match(sval)
    if match is not None:
        return int(match.groups()[0]) * (1024 ** 4)
    return int(sval)


def time_value(sval):
    """Convert suffixed time string to seconds value.

    s = seconds
    m = minutes
    h = hours
    d = days

    Args:
        sval (str): Time expression with suffix

    Returns:
        float: Time in seconds with millisecond.

    Raises:
        ConfigError: If conversion failed.
    """
    if sval is None:
        return None

    match = time_ptrn_s.match(sval)
    if match is not None:
        return int(match.groups()[0])
    match = time_ptrn_m.match(sval)
    if match is not None:
        return int(match.groups()[0]) * 60
    match = time_ptrn_h.match(sval)
    if match is not None:
        return int(match.groups()[0]) * 60 * 60
    match = time_ptrn_d.match(sval)
    if match is not None:
        return int(match.groups()[0]) * 60 * 60 * 24
    return float(sval)


def validate_tag(tag):
    """Validate tag syntax."""
    if type(tag) is not str:
        raise ConfigError("Tag must be a string.")


def parse_and_validate_cmds(cmds, check_input, check_output=None):
    """Parse and validate plugin commands.

    Vadation rule:
    - Starts with input plugin.
    - Zero or more modifier plugins.
    - Optionally finished with output plugin.

    Args:
        cmds (str): Plugin commands.
        check_input (bool): Check starting command.
        check_output (bool): Check ending command.

    Raises:
        ConfigError: When commands has a fault.

    Returns:
        list: Parsed command list.
    """
    logging.debug("parse_and_validate_cmds")
    if type(cmds) is not str:
        raise ConfigError("Commands are not a string.")

    cmds = cmds.split('|')
    last_idx = len(cmds) - 1
    pcmds = []
    check_output = check_input if check_output is None else check_output
    for i, cmd in enumerate(cmds):
        args = [arg.strip() for arg in cmd.split()]
        if len(args) == 0:
            raise ConfigError("Illegal plugin commands: {}".format(cmds))
        cmd = args[0]
        if check_input and i == 0 and not cmd.startswith('i.'):
            raise ConfigError("plugin commands must starts with input "
                              "plugin.")
        if check_output and i == last_idx:
            # Last command must be a tag command or output plugin
            if cmd != 'tag' and not cmd.startswith('o.'):
                raise ConfigError("'sources' plugin commands must ends with a "
                                  "tag command or output plugin.")
            tag = ' '.join(args[1:])
            validate_tag(tag)
        pcmds.append(args)
    return pcmds


def stop_iter_when_signalled(event):
    """Stop iteration when event is signalled."""
    if event is not None:
        if event.wait(0.0):
            raise StopIteration()
