"""This module implements plugin base."""

import os
import sys
import glob
from collections import namedtuple, defaultdict
import hashlib
import logging
import py_compile

from swak.config import get_exe_dir
from swak.exception import UnsupportedPython
from swak.const import TEST_STREAM_TAG


PREFIX = ['in', 'par', 'mod', 'buf', 'out']

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
        3. Separate text by new line,
        4. Filter lines if filter function exists.
        5. Yield them. If this is an input plugin for data of a known type,
           such as ``syslog``, it shall parse itself and return the record,
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


class BaseModifier(Plugin):
    """Base class for modify plugin.

    Following methods should be implemented:
        modify
    """

    def prepare_for_stream(self, tag, es):
        """Prepare to modify an event stream.

        Args:
            tag (str): Event tag
            es (EventStream): Event stream
        """
        pass

    def modify(self, tag, time, record):
        """Modify an event.

        Args:
            tag (str): Event tag
            time (float): Event time
            record (dict): Event record

        Returns:
            If modified
                float: Modified time
                record: Modified record

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
        write_stream, write_chunk

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
    'in': BaseInput,
    'par': BaseParser,
    'mod': BaseModifier,
    'buf': BaseBuffer,
    'out': BaseOutput,
}


def _get_base_class_name(prefix):
    cls = BASE_CLASS_MAP[prefix]
    return cls.__name__


def get_plugins_dir(standard, _home=None):
    """Return plugins directory path."""
    edir = get_exe_dir()
    dirn = 'stdplugins' if standard else 'plugins'
    return os.path.join(edir, dirn)


def enumerate_plugins(standard, _home=None, _filter=None):
    """Enumerate plugin infos.

    While visiting each sub-directory of the plugin directory, yield plugin
    information if the directory conform plugin standard.

    Args:
        _home (str): Explict home directory. Defaults to None.
        _filter (function): filter plugins for test.

    Returns:
        PluginInfo:
    """
    pdir = get_plugins_dir(standard, _home)
    if not os.path.isdir(pdir):
        raise ValueError("Plugin directory '{}' is not exist.".format(pdir))

    for _dir in os.listdir(pdir):
        if os.path.isfile(_dir):
            continue
        if _dir[0] == '_' or _dir[0] == '.':
            continue
        if _filter is not None and not _filter(_dir):
            continue

        adir = os.path.join(pdir, _dir)
        logging.debug("try to validate plugin {}".format(adir))
        for pi in validate_plugin_info(adir):
            yield pi


def validate_plugin_info(adir):
    """Check a directory whether it conforms plugin rules.

    Valid plugin rules:

    1. The directory has a python script with a name of standard plugin module
        name:

        plugin type prefix(`in`, `par`, `mod`, `buf`, `out`) + '_' +
        module name(snake case).
        ex) in_fake_data.py

    2. TODO

    Args:
        adir: Absolute directory path to test.

    Returns:
        list: List of PluginInfos if the plugin direcotry is valid.
    """
    pis = []
    for pypath in glob.glob(os.path.join(adir, '*.py')):
        fname = os.path.basename(pypath)
        if fname.startswith('__'):
            continue
        for pr in PREFIX:
            if not fname.startswith(pr):
                continue
            logging.debug("found valid plugin module {}".format(fname))
            mod = load_module(fname, pypath)
            pclass = _infer_plugin_class(mod, pr, fname)
            cname = pclass.__name__
            pname = '{}.{}'.format(pr, cname.lower())
            dname = os.path.basename(adir)
            cname = "{}.{}".format(pname, cname)
            pi = PluginInfo(fname, pname, dname, cname, mod.main.help, mod)
            pis.append(pi)
    return pis


def _infer_plugin_class(mod, pr, fname):
    """Infer plugin class name from module name.

    Args:
        mod (module): Plugin module
        pr (str): Prefix
        fname (str): Module file name
    Returns:
    """
    name = fname.replace(pr + '_', '').split('.')[0]

    if pr in BASE_CLASS_MAP:
        bclass = BASE_CLASS_MAP[pr]
    else:
        raise ValueError("Unknown prefix: '{}'".format(pr))

    for n in dir(mod):
        obj = getattr(mod, n)
        n = n.lower()
        try:
            if issubclass(obj, bclass) and n == name:
                return obj
        except TypeError:
            pass


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


def dump_plugins_import(standard, io, _filter=None):
    """Enumerate all plugins and dump import code to io.

    Args:
        standard (bool): Dump for standard plugin or not.
        io (IOBase): an IO instance where import code is written to.
        _filter (function): Filter function for plugins test.
    """
    logging.debug("dump_plugins_import _filter {}".format(_filter))
    io.write(u"# WARNING: Auto-generated code. Do not edit.\n\n")

    plugins = []
    for pi in enumerate_plugins(standard, _filter=_filter):
        logging.debug(pi)
        fname = os.path.splitext(pi.fname)[0]
        base_name = 'swak.{}plugins'.format('std' if standard else '')
        io.write(u"from {}.{} import {}\n".format(base_name, pi.dname, fname))
        plugins.append((pi.pname, fname, pi.cname))

    io.write(u'\nMODULE_MAP = {\n')
    for pl in plugins:
        io.write(u"    '{}': {},\n".format(pl[0], pl[1]))
    io.write(u'}\n')


def calc_plugins_hash(plugin_infos):
    """Make plugins hash.

    Hash value is made by md5 algorithm with plugin module names.
    If no plugin_infos exist, return 'NA'

    Args:
        plugin_infos: generator of PluginInfo

    Returns:
        str: Hexadecimal hash value
    """
    m = hashlib.md5()
    cnt = 0
    for pi in plugin_infos:
        m.update(pi.fname.encode('utf8'))
        cnt += 1
    if cnt == 0:
        return 'NA'
    return m.hexdigest()


def get_plugins_initpy_path(standard):
    """Return path of plugins/__init__.py."""
    return os.path.join(get_plugins_dir(standard), '__init__.py')


def remove_plugins_info():
    """Remove plugins information."""
    _remove_plugins_initpy(True)
    _remove_plugins_initpy(False)


def _remove_plugins_initpy(standard):
    """Remove plugins/__init__.py file and checksum file."""
    def remove(path):
        if os.path.isfile(path):
            os.unlink(path)
            logging.debug("removed {}".format(path))
        else:
            logging.debug("{} does not exist.".format(path))

    remove(get_plugins_initpy_path(standard))


def init_plugins_info(_filter=None):
    """Search and init plugins information at __init__.py."""
    _create_plugins_initpy(True, _filter)
    _create_plugins_initpy(False, _filter)


def _create_plugins_initpy(standard, _filter):
    """Enummerate all legal plugins and create (std)plugins/__init__.py file.

    Args:
        standard (bool): Check for standard plugin or not.
        _filter (func): Filter function for test.

    Returns:
        str: Plugins checksum
    """
    logging.debug("_create_plugins_initpy")
    path = get_plugins_initpy_path(standard)
    logging.debug("plugin initpy path: {}".format(path))

    logging.debug("writing {}".format(path))
    with open(path, 'wt') as f:
        dump_plugins_import(standard, f, _filter)
    py_compile.compile(path)


class DummyOutput(BaseOutput):
    """Output plugin for test."""

    def __init__(self, echo=False):
        """init.

        Args:
            echo: Whether print output or not.
        """
        super(DummyOutput, self).__init__()
        self.events = defaultdict(list)
        self.echo = echo

    def write_stream(self, tag, es):
        """Write event stream."""
        for time, record in es:
            self.events[tag].append((time, record))
            stag = '' if tag == TEST_STREAM_TAG else "tag: {}, ".format(tag)
            if self.echo:
                print("{}time: {}, record: {}".format(stag, time, record))

    def reset(self, tag=None):
        """Reset events."""
        if tag is not None:
            self.envents[tag] = []
        else:
            self.events = defaultdict(list)


def _get_full_name(prefix, class_name):
    name = _get_base_class_name(prefix)
    if class_name:
        return name
    return name[4:].lower()


def init_plugin_dir(prefixes, file_name, class_name, pdir):
    """Init plugin directory.

    Create following boilerplate files. (Plugin directory can have multiple
        plugin files to accomplish single purpose.)
    - One or more plugin type module
    - __init__.py
    - README.me file

    Args:
        prefixed (list): List of plugin prefixes
        file_name (str): Plugin file name
        class_name (str): Plugin class name
        pdir (str): Plugin directory
    """
    from jinja2 import Environment, PackageLoader
    env = Environment(loader=PackageLoader('swak', 'static/templates'))

    base_dir = get_plugins_dir(False)
    plugin_dir = os.path.join(base_dir, file_name)
    os.mkdir(plugin_dir)

    # create each type module
    for prefix in prefixes:
        fname = '{}_{}.py'.format(prefix, file_name)
        module_file = os.path.join(plugin_dir, fname)
        tmpl_name = 'tmpl_{}.py'.format(_get_base_class_name(prefix)[4:].
                                        lower())
        tpl = env.get_template(tmpl_name)
        basen = _get_full_name(prefix, True)
        typen = _get_full_name(prefix, False)
        with open(module_file, 'wt') as f:
            code = tpl.render(class_name=class_name, type_name=typen,
                              base_name=basen)
            f.write(code)

    # create README
    readme_file = os.path.join(plugin_dir, 'README.md')
    with open(readme_file, 'wt') as f:
        tpl = env.get_template('tmpl_readme.md')
        code = tpl.render(class_name=class_name, type_name=typen,
                          base_name=basen, file_name=file_name)
        f.write(code)

    # create __init__.py
    init_file = os.path.join(plugin_dir, '__init__.py')
    with open(init_file, 'wt') as f:
        pass
