import os
import sys
from platform import platform


def make_dir(adir):
    if not os.path.isdir(adir):
        os.mkdir(adir)
        return True


def is_windows():
    plt = platform()
    return 'Windows' in plt


def query_pid_dir():
    is_root = os.geteuid() == 0
    plt = platform()
    adir = None
    if 'Linux' in plt:
        if is_root:
            adir = '/var/run'
        else:
            adir = os.path.expanduser('~/.swak')
    elif 'Darwin' in plt:
        if is_root:
            adir = '/Library/Application Support/Swak'
        else:
            adir = os.path.expanduser('~/Library/Application Support/Swak')
    elif 'Windows' in plt:
        raise NotImplemented()
    else:
        raise Exception("Unidentified OS: {}".format(plt))

    make_dir(adir)
    return adir


def query_pid_path(build_postfix=''):
    pid_dir = query_pid_dir()
    pid_path = os.path.join(pid_dir, 'swak{}.pid'.format(build_postfix))
    return pid_path


def get_winsvc_status(svcname):
    import win32serviceutil
    import pywintypes

    try:
        ret = win32serviceutil.QueryServiceStatus(svcname)
    except pywintypes.error:
        return None
    return ret


def get_exedir():
    """Get package dir with regard to executable environment.

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
