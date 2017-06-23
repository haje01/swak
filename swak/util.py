import os
from platform import platform


def make_dir(adir):
    if not os.path.isdir(adir):
        os.mkdir(adir)
        return True


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
