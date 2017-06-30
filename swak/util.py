import os
import sys
from platform import platform
import collections
import errno


PY2 = sys.version_info[0] == 2


def make_dirs(adir):
    """Make directory if not exist."""
    try:
        os.makedirs(adir)
    except OSError as err:
        if err.errno != errno.EEXIST:
            raise
        else:
            # directory already exists
            pass


def is_windows():
    plt = platform()
    return 'Windows' in plt


def get_pid_dir(home):
    return os.path.join(select_home(home), 'run')


def get_pid_path(home, svc_name):
    """Get pid path with regards home and service name."""
    pid_name = 'swak.pid' if svc_name == None else '{}.pid'.format(svc_name)
    pid_path = os.path.join(home, 'run', pid_name)
    return pid_path


def get_winsvc_status(svcname):
    import win32serviceutil
    import pywintypes

    try:
        ret = win32serviceutil.QueryServiceStatus(svcname)
    except pywintypes.error:
        return None
    return ret


def update_dict(d, u):
    """Update dictionary recursively.

    Update dictionary `d` with the value of `u` of matching key & hierarchy.

    Args:
        d (dict): Original dictionary to be updated.
        u (dict): Referential dictionary

    Returns:
        dict: Dictionary `d`

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
