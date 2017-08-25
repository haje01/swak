"""Plugin module."""

import os
import sys
import glob
from collections import namedtuple, defaultdict
import hashlib
import logging
import py_compile

from swak.config import get_exe_dir
from swak.exception import UnsupportedPython


PREFIX = ['in_', 'par_', 'ref_', 'buf_', 'out_', 'cmd_']
CHKSUM_FNAME = '_CHECKSUM_.txt'

PluginInfo = namedtuple('PluginInfo', ['fname', 'pname', 'dname', 'cname',
                                       'desc', 'module'])


class Plugin(object):
    """Base class for plugin."""

    def __init__(self):
        """Init."""
        self.started = self.terminated = False

    def start(self):
        """Start plugin.

        This method is called when the task starts after processing the
        setting. Creation of resources such as files and threads to be used in
        the plug-in is created here.
        """
        self.started = True

    def stop(self):
        """Stop plugin.

        This method is called when the task is preparing to terminate. You
        should do simple things that do not fail, such as setting a thread
        stop flag.

        """
        self.started = False

    def terminate(self):
        """Terminate plugin.

        This method is called when the task is completely terminated. Here you
        can close or remove any files, threads, etc. that you had created in
        ``start``.
        """
        self.terminated = True


class BaseInput(Plugin):
    """Base class for input plugin.

    Implementation of following functions is required:

        ``read``
    """

    def __init__(self):
        """Init."""
        super(BaseInput, self).__init__()
        self.filter_fn = None

    def read(self):
        """Read data from source.

        It is implemented in the following format.

        1. Read the line-delimited text from the source.
        2. If the ``encoding`` is specified, convert it to ``utf8`` text.
        3. Separate text line by line,
        4. For the lines that pass ``filter``
        5. Yield them. If this is an input plugin for data of a known type,
           such as ``syslog``, it will parse itself and return the record,
           otherwise it will just return the line.

        """
        raise NotImplemented()

    def filter(self, line):
        """Filter unparsed raw line.

        You can override this function or set filter function by
            `set_filter_func`.

        Args:
            line (str): Unparsed line.

        Returns:
            (str): Returns only passed line.
        """
        if self.filter_fn is not None:
            if self.filter_fn(line):
                return line

    def set_filter_func(self, func):
        """Set filter function."""
        self.filter_fn = func


class BaseParser(Plugin):
    """Base class for parser plugin.

    Following methods should be implemented:
        execute

    """

    def parse(self):
        """Parse."""
        raise NotImplemented()


class BaseReform(Plugin):
    """Base class for reform plugin.

    Following methods should be implemented:
        reform
    """

    def reform(self, tag, time, record):
        """Reform an event.

        Args:
            tag (str): Event tag
            time (float): Event time
            record (dict): Event record

        Returns:
            If reformed
                float: Reformed time
                record: Reformed record

            If removed
                None
        """
        raise NotImplemented()


class BaseBuffer(Plugin):
    """Base class for buffer plugin.

    Following methods should be implemented:
        append

    """

    def append(self, record):
        """Append a record."""
        raise NotImplemented()


class BaseOutput(Plugin):
    """Base class for output plugin.

    Following methods should be implemented:
        write_record, write_chunk

    """

    def write_stream(self, tag, es):
        """Write event stream synchronously.

        Args:
            tag (str): Event tag.
            es (EventStream): Event stream.
        """
        raise NotImplemented()

    def write_chunk(self, chunk):
        """Write a chunk from buffer."""
        raise NotImplemented()


class BaseCommand(Plugin):
    """Base class for command plugin.

    Following methods should be implemented:
        execute

    """

    def execute(self):
        """Execute command."""
        raise NotImplemented()


BASE_CLASS_MAP = {
    'in_': BaseInput,
    'par_': BaseParser,
    'ref_': BaseReform,
    'buf_': BaseBuffer,
    'out_': BaseOutput,
    'cmd_': BaseCommand,
}


def get_plugins_dir(_home=None):
    """Return plugins directory path."""
    edir = get_exe_dir()
    return os.path.join(edir, 'plugins')


def enumerate_plugins(_home=None, _filter=None):
    """Enumerate plugin infos.

    While visiting each sub-directory of the plugin directory, yield plugin
    information if the directory conform plugin standard.

    Args:
        _home (str): Explict home directory. Defaults to None.
        _filter (function): filter plugins for test.

    Returns:
        PluginInfo:
    """
    pdir = get_plugins_dir(_home)
    if not os.path.isdir(pdir):
        raise ValueError("Plugin directory '{}' is not exist.".format(pdir))

    for _dir in os.listdir(pdir):
        if _dir.startswith('_'):
            continue
        if _filter is not None and not _filter(_dir):
            continue

        adir = os.path.join(pdir, _dir)
        logging.debug("validate plugin {}".format(adir))
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
        PluginInfo: If the plugin direcotry is valid.
        None: If not.
    """
    for pypath in glob.glob(os.path.join(adir, '*.py')):
        fname = os.path.basename(pypath)
        for pr in PREFIX:
            if not fname.startswith(pr):
                continue
            logging.debug("found valid plugin module {}".format(fname))
            mod = load_module(fname, pypath)
            pclass = _infer_plugin_class(mod, pr, fname)
            prefix = pr.replace('_', '.')
            cname = pclass.__name__
            pname = '{}{}'.format(prefix, cname.lower())
            dname = os.path.basename(adir)
            cname = "{}{}.{}".format(pr, cname.lower(), cname)
            return PluginInfo(fname, pname, dname, cname, mod.main.help, mod)


def _infer_plugin_class(mod, pr, fname):
    name = fname.replace(pr, '').split('.')[0]

    if pr in BASE_CLASS_MAP:
        bclass = BASE_CLASS_MAP[pr]
    else:
        raise ValueError("Unknown prefix: '{}'".format(pr))

    for n in dir(mod):
        obj = getattr(mod, n)
        n = n.lower()
        if issubclass(obj, bclass) and n == name:
            return obj


def load_module(name, path):
    """Load a module considering python versions.

    Args:
        name: Module name
        path: Absolute path to the module.

    Returns:
        module: Imported module.
    """
    logging.debug("load module: {} from {}".format(name, path))

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


def dump_plugins_import(io, chksum=None, _filter=None):
    """Enumerate all plugins and dump import code to io.

    Args:
        io (IOBase): an IO instance where import code is written to.
        chksum (str): Explicitly given checksum.
        _filter (function): Filter function for plugins test.
    """
    io.write(u"# WARNING: Auto-generated code. Do not edit.\n\n")

    plugins = []
    for pi in enumerate_plugins(_filter=_filter):
        fname = os.path.splitext(pi.fname)[0]
        io.write(u"from swak.plugins.{} import {}\n".format(pi.dname, fname))
        plugins.append((pi.pname, fname, pi.cname))

    io.write(u'\nMODULE_MAP = {\n')
    for pl in plugins:
        io.write(u"    '{}': {},\n".format(pl[0], pl[1]))
    io.write(u'}\n')


def calc_plugins_hash(plugin_infos):
    """Make plugins hash.

    Hash value is made by md5 algorithm with plugin module names.

    Args:
        plugin_infos: generator of PluginInfo

    Returns:
        str: Hexadecimal hash value
    """
    m = hashlib.md5()
    for pi in plugin_infos:
        m.update(pi.fname.encode('utf8'))
    return m.hexdigest()


def get_plugins_initpy_path():
    """Return path of plugins/__init__.py."""
    return os.path.join(get_plugins_dir(), '__init__.py')


def remove_plugins_initpy():
    """Remove plugins/__init__.py file and checksum file."""
    def remove(path):
        if os.path.isfile(path):
            os.unlink(path)
            logging.debug("removed {}".format(path))
        else:
            logging.debug("{} does not exist.".format(path))

    remove(get_plugins_initpy_path())
    remove(get_plugins_chksum_path())


def get_plugins_chksum_path():
    """Return plugin checksum path."""
    return os.path.join(get_plugins_dir(), CHKSUM_FNAME)


def check_plugins_initpy(plugin_infos):
    """Create plugins/__init__.py file if plugins checksum has been changed.

    Checksum is serialized to a dedicated file.

    Args:
        plugin_infos: Generator of PluginInfo

    Returns:
        bool: Where file has been created.
        str: Plugins checksum
    """
    logging.debug("check_plugins_initpy")
    create = False
    path = get_plugins_initpy_path()
    logging.debug("plugin initpy path: {}".format(path))
    chksum = calc_plugins_hash(plugin_infos)
    cpath = get_plugins_chksum_path()
    if not os.path.isfile(path):
        logging.debug("{} does not exist.".format(path))
        create = True
    else:
        if not os.path.isfile(cpath):
            create = True
        else:
            with open(cpath, 'rt') as f:
                ochksum = f.read().strip()
            logging.debug("plugins old chksum {}, new chksum"
                          " {}".format(ochksum, chksum))
            create = ochksum != chksum

    if create:
        logging.debug("writing {}".format(path))
        with open(path, 'wt') as f:
            dump_plugins_import(f, chksum)
        py_compile.compile(path)

        logging.debug("writing {} - {}".format(cpath, chksum))
        with open(cpath, 'wt') as f:
            f.write('{}\n'.format(chksum))

    return create, chksum


class DummyOutput(BaseOutput):
    """Output plugin for test."""

    def __init__(self):
        """init."""
        super(DummyOutput, self).__init__()
        self.events = defaultdict(list)

    def emit_events(self, tag, es):
        """Emit events."""
        for time, record in es:
            print("tag {}, time {}, record {}".format(tag, time, record))
            self.events[tag].append((time, record))

    def emit(self, tag, es):
        """Process event stream."""
        for time, record in es:
            self.events[tag].append((time, record))

    def reset(self, tag=None):
        """Reset events."""
        if tag is not None:
            self.envents[tag] = []
        else:
            for tag in self.events.keys():
                self.events[tag] = []
