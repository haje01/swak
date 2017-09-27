"""This module implements plugin base."""

import os
import sys
import glob
from collections import namedtuple, defaultdict, deque
import logging
import types
import json
import time as mtime

from swak.config import get_exe_dir
from swak.exception import UnsupportedPython
from swak.const import PLUGIN_PREFIX
from swak.chunk import Chunk


PREFIX = ['in', 'par', 'mod', 'for', 'buf', 'out']

PluginInfo = namedtuple('PluginInfo', ['fname', 'pname', 'dname', 'cname',
                                       'desc', 'module'])


class Plugin(object):
    """Base class for plugin."""

    def __init__(self):
        """Init."""
        self.router = None
        self.started = self.shutdowned = False

    def set_router(self, router):
        """Set router for the plugin."""
        self.router = router

    def start(self):
        """Start plugin.

        This method is called when the task starts after processing the
        setting. Creation of resources such as files and threads to be used in
        the plug-in is created here.
        """
        assert not self.started
        self.started = True

    def stop(self):
        """Stop plugin.

        This method is called when the task is preparing to shutdown. You
        should do simple things that do not fail, such as setting a thread
        stop flag.

        """
        assert self.started
        self.started = False

    def shutdown(self):
        """Shutdown plugin.

        This method is called when the task is completely shutdown. Here you
        can close or remove any files, threads, etc. that you had created in
        ``start``.
        """
        self.shutdowned = True


class Input(Plugin):
    """Base class for input plugin."""

    def __init__(self):
        """Init.

        Args:
            tag (str): An event tag.
        """
        super(Input, self).__init__()
        self.tag = None
        self.encoding = None

    def set_tag(self, tag):
        """Set tag."""
        self.tag = tag

    def read(self):
        """Read input from source and emit to event router."""
        raise NotImplementedError()

    def emit(self, record):
        """Emit a record.

        Args:
            record (dict)
        """
        assert self.router is not None, "Plugin needs a router."
        assert self.tag is not None, "Input plugin needs a event tag."
        time = mtime.time()
        self.router.emit(self.tag, time, record)

    def set_encoding(self, encoding):
        """Set encoding of input source.

        Args:
            encoding (str): Encoding of input source.
        """
        self.encoding = encoding


class RecordInput(Input):
    """Base class for input plugin which emits record.

    This if usually for a generative input plugin which generate data and
        **emit** record directly to the event router. (no following parser is
        needed.)

    Function to be implemented:

        ``read_record``
    """

    def read(self):
        """Read records and emit them to the router."""
        for record in self.generate_records():
            self.emit(record)

    def generate_records(self):
        """Yield multiple records.

        Yields:
            dict: A record
        """
        raise NotImplementedError()


class TextInput(Input):
    """Base class for input plugin which reads text and emits line.

    This is usally for a plugin which reads text from source, seperate it by
        lines and **feed** them to the following parser.

    Function to be implemented:

        ``read_line``
    """

    def __init__(self):
        """Init."""
        super(TextInput, self).__init__()
        self.parser = None
        self.filter_fn = None

    def set_parser(self, parser):
        """Set parser for this TextInput plugin."""
        self.parser = parser

    def read(self):
        """Read data from source, parse and emit results to the router."""
        assert self.parser is not None, "Text input plugin needs a parser."
        for line in self.read_lines():
            if line is None:
                break
            if self.encoding is not None:
                line = line.decode(self.encoding)
            if self.filter_fn is not None:
                if not self.filter_fn(line):
                    continue

            record = self.parser.parse(line)
            self.emit(record)

    def read_lines(self):
        """Read lines.

        Yields:
            str: A line
        """
        raise NotImplementedError()

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


class Parser(Plugin):
    """Base class for parser plugin.

    Following methods should be implemented:
        execute

    """

    def parse(self, line):
        """Parse.

        Args:
            line (str): Line to parse.

        Returns:
            dict: Parsed result.
        """
        raise NotImplemented()


class Modifier(Plugin):
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


class Formatter(Plugin):
    """Base class for formatter plugin.

    Following methods should be implemented:
        call
    """

    def format(self, tag, time, record):
        """Format given data."""
        raise NotImplemented()


class Buffer(Plugin):
    """Base class for buffer plugin.

    Following methods should be implemented:
        append
    """

    def __init__(self, binary):
        """Init.

        Args:
            binary (bool): Store data as binary or not.
        """
        self.binary = binary
        self.recv_queue = None
        self.tag = None
        self.chunks = deque([Chunk(binary)])
        self.num_flush = 0

    def set_tag(self, tag):
        """Set tag."""
        self.tag = tag

    def set_recv_queue(self, recv_queue):
        """Set recv queue.

        Receive event streams from input thread.

        Args:
            recv_queue (Queue): recv queue
        """
        self.recv_queue = recv_queue

    @property
    def connected_with_output_proxy(self):
        """Return whether this buffer connected with output proxy or not."""
        return self.recv_queue is not None

    def read_queue(self):
        """Read from receive queue.

        This must be called within output thread.
        """
        assert self.recv_queue is not None
        es = self.recv_queue.get()
        self.append(es)

    @property
    def num_chunk(self):
        """Return number of chunks."""
        return len(self.chunks)

    def append(self, es):
        """Append event stream to buffer.

        If matches flush condition, will call ``flush`` with chunk

        Args:
            es (EventStream): Event stream.
        """
        chunk = self.chunks[-1]
        chunk.append()
        raise NotImplemented()

    def flush(self, chunk):
        """Flush chunk into the output."""
        assert self.output
        self.num_flush += 1


class Output(Plugin):
    """Base class for output plugin.

    Following methods should be implemented:
        write_stream, write_chunk

    """

    def __init__(self):
        """Init."""
        super(Output, self).__init__()
        self.send_queue = None
        self.buffer = None

    def set_buffer(self, buffer):
        """Set output bufer."""
        self.buffer = buffer

    def set_send_queue(self, send_queue):
        """Set send queue.

        It means this plugin works as output proxy in an input thread. the
            queue will be consumed by an output thread's buffer.

        Args:
            send_queue (Queue): queue of event streams.
        """
        self.send_queue = send_queue

    @property
    def is_proxy(self):
        """Return whether this is an output proxy or not."""
        return self.send_queue is not None

    def write_stream(self, tag, es):
        """Write event stream to queue or directly to output target.

        If send queue exists, this acts as output proxy, putting event stream
            to the queue.

        Args:
            tag (str): Event tag.
            es (EventStream): Event stream.
        """
        if self.send_queue is None:
            self._write_stream(self, tag, es)
        else:
            self.send_queue.put(es)

    def _write_stream(self, tag, es):
        """Write event stream synchronously.

        Args:
            tag (str): Event tag.
            es (EventStream): Event stream.
        """
        raise NotImplemented()

    def _write_chunk(self, chunk):
        """Write a chunk from buffer."""
        raise NotImplemented()


BASE_CLASS_MAP = {
    'in': Input,
    'intxt': TextInput,
    'inrec': RecordInput,
    'par': Parser,
    'mod': Modifier,
    'buf': Buffer,
    'out': Output,
}


def _get_base_class_name(prefix):
    """Get base class name from prefix."""
    cls = BASE_CLASS_MAP[prefix]
    return cls.__name__


def _get_full_name(prefix, class_name):
    """Get class name for template rendering from prefix."""
    name = _get_base_class_name(prefix)
    if class_name:
        return name
    return name.lower()


def get_plugins_dir(standard, _home=None):
    """Return plugins directory path."""
    edir = get_exe_dir()
    dirn = 'stdplugins' if standard else 'plugins'
    return os.path.join(edir, dirn)


def iter_plugins(standard, _home=None, _filter=None):
    """Iterate valid plugin infos.

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
            logging.debug("  got plugin info {}".format(pi))
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
        list: List of PluginInfo for valid plugin
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
        classobj
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
    logging.error("Can not infer class instance - mod {} pr {} fname {}".
                  format(mod, pr, fname))


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


class DummyOutput(Output):
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
            if self.echo:
                print("{}\t{}\t{}".format(time, tag, json.dumps(record)))

    def reset(self, tag=None):
        """Reset events."""
        if tag is not None:
            self.envents[tag] = []
        else:
            self.events = defaultdict(list)


def init_plugin_dir(prefixes, file_name, class_name, pdir):
    """Init plugin directory.

    Create following boilerplate files. (Plugin directory can have multiple
        plugin files to accomplish single purpose.)

    - One or more plugin type module
    - __init__.py
    - README.md file
    - test_(file_name).py file

    Args:
        prefixes (list): List of plugin prefixes
        file_name (str): Plugin file name
        class_name (str): Plugin class name
        pdir (str): Plugin directory
    """
    from jinja2 import Environment, PackageLoader
    env = Environment(loader=PackageLoader('swak', 'static/templates'))

    base_dir = get_plugins_dir(False)
    plugin_dir = os.path.join(base_dir, '{}-{}'.format(PLUGIN_PREFIX,
                                                       file_name))
    os.mkdir(plugin_dir)

    def base_input_prefix(prefix):
        return 'in' if prefix in ['intxt', 'inrec'] else prefix

    # create each type module
    for _prefix in prefixes:
        prefix = base_input_prefix(_prefix)
        fname = '{}_{}.py'.format(prefix, file_name)
        module_file = os.path.join(plugin_dir, fname)
        tmpl_name = 'tmpl_{}.py'.format(_get_base_class_name(_prefix).lower())
        tpl = env.get_template(tmpl_name)
        basen = _get_full_name(_prefix, True)
        typen = _get_full_name(_prefix, False)
        with open(module_file, 'wt') as f:
            code = tpl.render(class_name=class_name, type_name=typen,
                              base_name=basen)
            f.write(code)

    # create README
    readme_file = os.path.join(plugin_dir, 'README.md')
    with open(readme_file, 'wt') as f:
        tpl = env.get_template('tmpl_readme.md')
        code = tpl.render(plugin_prefix=PLUGIN_PREFIX, class_name=class_name,
                          type_name=typen, base_name=basen,
                          file_name=file_name)
        f.write(code)

    # create test file
    test_file = os.path.join(plugin_dir, 'test_{}.py'.format(file_name))
    with open(test_file, 'wt') as f:
        tpl = env.get_template('tmpl_unittest.py')
        typens = [_get_full_name(pr, False) for pr in prefixes]
        prefixes = [base_input_prefix(pr) for pr in prefixes]
        code = tpl.render(class_name=class_name, prefixes=prefixes,
                          type_names=typens, file_name=file_name)
        f.write(code)

    # create __init__.py
    init_file = os.path.join(plugin_dir, '__init__.py')
    with open(init_file, 'wt') as f:
        pass


def import_plugins_package(standard):
    """Virtually import and return plugins base package.

    Args:
        standard (bool): True for standard plugins, False for external plugins

    Returns:
        module: Loaded module.
    """
    mod_name = 'stdplugins' if standard else 'plugins'
    plugins = types.ModuleType(mod_name)
    plugins.__path__ = [get_plugins_dir(standard)]
    sys.modules[mod_name] = plugins
    return plugins
