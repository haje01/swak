import os
import sys
from platform import platform
import collections


def make_dirs(adir):
    """Make directory if not exist."""
    try:
        os.makedirs(adir)
    except FileExistsError:
        pass


def is_windows():
    plt = platform()
    return 'Windows' in plt


def query_pid_dir():
    adir = os.path.join(get_home_dir(), 'run')
    #is_root = os.geteuid() == 0
    #plt = platform()
    #adir = None
    #if 'Linux' in plt:
        #if is_root:
            #adir = '/var/run'
        #else:
            #adir = os.path.expanduser('~/.swak')
    #elif 'Darwin' in plt:
        #if is_root:
            #adir = '/Library/Application Support/Swak'
        #else:
            #adir = os.path.expanduser('~/Library/Application Support/Swak')
    #elif 'Windows' in plt:
        #raise NotImplemented()
    #else:
        #raise Exception("Unidentified OS: {}".format(plt))

    make_dirs(adir)
    return adir


def query_pid_path(svc_name=None):
    pid_name = 'swak.pid' if svc_name == None else '{}.pid'.format(svc_name)
    pid_dir = query_pid_dir()
    pid_path = os.path.join(pid_dir, pid_name)
    return pid_path


def get_winsvc_status(svcname):
    import win32serviceutil
    import pywintypes

    try:
        ret = win32serviceutil.QueryServiceStatus(svcname)
    except pywintypes.error:
        return None
    return ret


def get_exe_dir():
    """Get swak executable's directory.

    Decide config directory with following rules:
        1. If package has been freezed, used dir of freezed executable path,
        2. Or use the dir of current module.

    Then make full path by join directory & config file name.

    Returns:
        str: Absolute path to config file.
    """
    if getattr(sys, 'frozen', False):
        bdir = os.path.dirname(sys.executable)
    else:
        bdir = os.path.dirname(os.path.abspath(__file__))
    return bdir


def get_home_dir():
    """Get swak home directory.

    Decide config directory with following rules:
        1. If envvar `SWAK_HOME` exists, use it.
        2. Or use executable's directory.

    Then make full path by join directory & config file name.

    Returns:
        str: Absolute path to config file.
    """
    bdir = os.environ.get('SWAK_HOME')
    if bdir is not None:
        return bdir

    return get_exe_dir()


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


def init_home_dirs(cfg):
    """Initialized required directories for home.

    Check following paths and make directories if needed.
        - run/
        - log/ (in view of logger/handlers/file/filename of config)
    """
    home = get_home_dir()
    make_dirs(os.path.join(home, 'run'))
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
