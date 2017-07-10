import os
import sys
import glob
from collections import namedtuple

from swak.config import get_exe_dir
from swak.exception import UnsupportedPython


PREFIX = ['in_', 'par_', 'tr_', 'buf_', 'out_', 'cmd_']

PluginInfo = namedtuple('PluginInfo', ['name', 'desc', 'module'])

class Plugin(object):

    def __init__(self):
        self.started = self.terminated = False

    def start(self):
        self.started = True

    def stop(self):
        self.started = False

    def terminate(self):
        self.terminated = True


class BaseInput(Plugin):

    def read(self):
        raise NotImplemented()


class BaseParser(Plugin):

    def parse(self):
        raise NotImplemented()


class BaseTransform(Plugin):

    def transform(self):
        raise NotImplemented()


class BaseBuffer(Plugin):

    def append(self, record):
        raise NotImplemented()


class BaseOutput(Plugin):

    def process(self, record):
        raise NotImplemented()

    def write(self, chunk):
        raise NotImplemented()


class BaseCommand(Plugin):

    def execute(self):
        raise NotImplemented()


def get_plugins_dir(_home=None):
    edir = get_exe_dir()
    return os.path.join(edir, 'plugins')


def enumerate_plugins(_home=None):
    """Enumerate plugin infos.

    Visit every sub-directory of a plugin directory. Yield a plugin information
    if the directory conform plugin standard.

    Returns:
        str: Plugin name
        str: Plugin absolute path
    """
    pdir = get_plugins_dir(_home)
    if not os.path.isdir(pdir):
        raise ValueError("Directory '{}' is not exist.".format(pdir))

    for _dir in os.listdir(pdir):
        if _dir.startswith('_'):
            continue
        adir = os.path.join(pdir, _dir)
        pi = validate_plugin_info(adir)
        if pi is not None:
            yield pi


def validate_plugin_info(adir):
    """Check a directory whether it conforms plugin rules.

    Valid plugin rules:
    1. The directory has a python script with a name of standard plugin module
        name:

        plugin type prefix(`in`, `par`, `tr`, `buf`, `out`, `cmd`) + '_' +
        module name(snake case).
        ex) in_fake_data.py

    2. TODO

    Args:
        adir: Absolute directory path to test.

    Returns:
        PluginInfo: If the direcotry is valid.
        None: If not.
    """
    for pypath in glob.glob(os.path.join(adir, '*.py')):
        fname = os.path.basename(pypath)
        for pr in PREFIX:
            if not fname.startswith(pr):
                continue
            mod = load_plugin(fname, pypath)
            pclass = _infer_plugin_class(mod, pr, fname)
            prefix = pr.replace('_', '.')
            pname = '{}{}'.format(prefix, pclass.__name__)
            return PluginInfo(pname, mod.main.help, mod)


def _infer_plugin_class(mod, pr, fname):
    name = fname.replace(pr, '').split('.')[0]

    if pr == 'in_':
        bclass = BaseInput
    elif pr == 'par_':
        bclass = BaseParser
    elif pr == 'tr_':
        bclass = BaseTransform
    elif pr == 'buf_':
        bclass = BaseBuffer
    elif pr == 'out_':
        bclass = BaseOutput
    elif pr == 'cmd_':
        bclass = BaseCommand

    for n in dir(mod):
        obj = getattr(mod, n)
        n = n.lower()
        if issubclass(obj, bclass) and n == name:
            return obj


def load_plugin(name, path):
    major, minor = sys.version_info[0:2]
    if major == 2:
        import imp
        return imp.load_source(name, path)
    if major == 3 and minor >= 5:
        import importlib.util
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    else:
        raise UnsupportedPython()
