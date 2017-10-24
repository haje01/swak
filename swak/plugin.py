"""This module implements plugin base."""

import os
import sys
import glob
from collections import namedtuple
import logging
import types

from swak.config import get_exe_dir
from swak.exception import UnsupportedPython
from swak.const import PLUGINDIR_PREFIX
from swak.formatter import StdoutFormatter
from swak.buffer import MemoryBuffer
from swak.util import get_plugin_module_name


PREFIX = ['i', 'p', 'm', 'o']

PluginInfo = namedtuple('PluginInfo', ['fname', 'pname', 'dname', 'cname',
                                       'desc', 'module'])


class Plugin(object):
    """Base class for plugin."""

    def __init__(self):
        """Init."""
        self.started = self.shutdowned = False
        self.tag = None

    def set_tag(self, tag):
        """Set tag."""
        self.tag = tag

    def start(self):
        """Start plugin.

        This method is called when the task starts after processing the
        setting. Creation of resources such as files and threads to be used in
        the plug-in is created here.
        """
        assert not self.started
        self._start()
        self.started = True

    def _start(self):
        """Implement start."""
        pass

    def stop(self):
        """Stop plugin.

        This method is called when the task is preparing to shutdown. You
        should do simple things that do not fail, such as setting a thread
        stop flag.

        """
        assert self.started
        self._stop()
        self.started = False

    def _stop(self):
        """Implement stop."""
        pass

    def shutdown(self):
        """Shutdown plugin.

        This method is called when the agent has been completely done. Here you
        can close or remove any files, threads, etc that you had created in
        ``start``.
        """
        assert not self.started  # stop first
        assert not self.shutdowned
        self._shutdown()
        self.shutdowned = True

    def _shutdown(self):
        """Implement shutdown."""
        pass


class Input(Plugin):
    """Base class for input plugin."""

    def __init__(self):
        """Init.

        Args:
            tag (str): An event tag.
        """
        super(Input, self).__init__()
        self.encoding = None

    def read_one(self):
        """Read a record from the source.

        Returns:
            dict: A record.
        """
        raise NotImplementedError()

    def set_encoding(self, encoding):
        """Set encoding of input source.

        Args:
            encoding (str): Encoding of input source.
        """
        self.encoding = encoding


class InputProxy(Input):
    """Input proxy class."""

    def __init__(self):
        """Init."""
        self.recv_queues = []

    def append_recv_queue(self, queue):
        """Append receive queue."""
        assert queue not in self.recv_queues, "The queue has already been "\
            "appended."
        self.recv_queues.append(queue)

    def read_queues(self):
        """Read from receive queues.

        This is to be called within output thread.
        """
        for tag, queue in self.recv_queues.items():
            es = queue.get()
            self.handle_stream(tag, es)


class RecordInput(Input):
    """Base class for input plugin which emits record.

    This if usually for a generative input plugin which knows how to genreate
      data and **emit** record directly to the event router. (no following
      parser is needed.)

    Function to be implemented:

        ``read_one``
    """

    def read_one(self):
        """Read a record and emit it to the router."""
        record = self.read_record()
        if record:
            return record

    def read_record(self):
        """Read a record from the source.

        Throw NoMoreData exception if no more record available.

        Raises:
            NoMoreData: No more data to read.

        Returns:
            dict: Read record. Return empty dict if conditions do not
                match.
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

    def read_one(self):
        """Read a line from source, and return a record by parsing.

        Returns:
            str: A line. Return empty string if conditions do not match.
        """
        assert self.parser is not None, "Text input plugin needs a parser."
        line = self.read_line()
        if line:
            if self.encoding is not None:
                line = line.decode(self.encoding)
            # test by filter function
            if self.filter_fn is not None:
                if not self.filter_fn(line):
                    return {}
            record = self.parser.parse(line)
            return record
        else:
            return {}

    def read_line(self):
        """Read a line from the source.

        Throw NoMoreData exception if no more record available.

        Raises:
            NoMoreData: No more data to read.

        Yields:
            str: A line. Return empty string if conditions do not match.
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
        raise NotImplementedError()


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

    def modify(self, tag, utime, record):
        """Modify an event.

        Args:
            tag (str): Event tag
            utime (float): Event time stamp.
            record (dict): Event record

        Returns:
            If modified
                float: Modified time
                record: Modified record

            If removed
                None
        """
        raise NotImplementedError()


class Output(Plugin):
    """Base class for output plugin.

    Following methods should be implemented:
        write_stream, write_chunk

    """

    def __init__(self, formatter, abuffer):
        """Init.

        Args:
            formatter (Formatter): Swak formatter for this output.
            abuffer (Buffer): Swak buffer for this output.
        """
        super(Output, self).__init__()
        if abuffer is not None and abuffer.output is None:
            abuffer.output = self
        self.formatter = formatter
        self.buffer = abuffer

    def _shutdown(self):
        """Implement shutdown."""
        if self.buffer.flush_at_shutdown is not None:
            self.flush()

    def flush(self):
        """Flushing buffer."""
        assert self.buffer is not None
        self.buffer.flushing()

    def set_buffer(self, buffer):
        """Set output bufer."""
        self.buffer = buffer

    # def set_send_queue(self, send_queue):
    #     """Set send queue.

    #     It means this plugin works as output proxy in an input thread. the
    #         queue will be consumed by an output thread's buffer.

    #     Args:
    #         send_queue (Queue): queue of event streams.
    #     """
    #     assert len(self.recv_queues) > 0, "Can not send and receive at the"\
    #         " same time"
    #     self.send_queue = send_queue

    def _start(self):
        """Implement start."""
        if self.buffer is not None:
            self.buffer.start()

    def _stop(self):
        """Implement stop."""
        if self.buffer is not None:
            self.buffer.stop()

    # @property
    # def is_proxy(self):
    #     """Return whether this is an output proxy or not."""
    #     return self.send_queue is not None

    def emit_events(self, tag, es):
        """Emit event stream to queue or directly to output target.

        Args:
            tag (str): Event tag.
            es (EventStream): Event stream.

        Returns:
            int: Adding size of the stream.
        """
        return self.handle_stream(tag, es)

    def handle_stream(self, tag, es):
        """Handle event stream from emit events.

        Format each event and write it to buffer.

        Args:
            tag (str)
            es (EventStream)

        Returns:
            int: Adding size of the stream.
        """
        adding_size = 0
        for utime, record in es:
            dtime = self.formatter.timestamp_to_datetime(utime)
            formatted = self.formatter.format(tag, dtime, record)
            adding_size += self.buffer.append(formatted)
        return adding_size

    def write(self, bulk):
        """Write a bulk.

        Make sure the bulk is empty and do nothing if it is empty.

        Args:
            bulk: A bulk from a chunk.
        """
        if len(bulk) == 0:
            return
        self._write(bulk)

    def _write(self, bulk):
        """Write a bulk.

        Args:
            bulk (bytearray or list): If the chunk that passes the argument is
              a binary type, bulk is an array of bytes, otherwise it is a list
              of strings.
        """
        raise NotImplementedError()

    def may_chunking(self):
        """Chunking if needed."""
        if self.buffer is not None:
            self.buffer.may_chunking()

    def may_flushing(self, last_flush_interval=None):
        """Flushing if needed.

        Args:
            force_flushing_interval (float): Force flushing interval for input
              is terminated.
        """
        if self.buffer is not None:
            self.buffer.may_flushing(last_flush_interval)


class OutputProxy(Output):
    """Output proxy class."""

    def __init__(self, queue):
        """Init.

        Args:
            queue (Queue): Sending queue.
        """
        self.send_queue = queue

    def emit_events(self, tag, es):
        """Emit event stream to queue or directly to output target.

        As output proxy, putting event stream to the queue.

        Args:
            tag (str): Event tag.
            es (EventStream): Event stream.
        """
        # send_queue exists, which means two threads for input & output.
        self.send_queue.put(es)


BASE_CLASS_MAP = {
    'i': Input,
    'it': TextInput,
    'ir': RecordInput,
    'p': Parser,
    'm': Modifier,
    'o': Output,
}


def _get_base_class_name(prefix):
    """Get base class name from prefix."""
    acls = BASE_CLASS_MAP[prefix]
    return acls.__name__


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


def iter_plugins(standard, _home=None, _filter=None, warn=True):
    """Iterate valid plugin infos.

    While visiting each sub-directory of the plugin directory, yield plugin
    information if the directory conform plugin standard.

    Args:
        _home (str): Explict home directory. Defaults to None.
        _filter (function): filter plugins for test.
        warn (bool): Warning if a directory does not suitable for plugin.

    Yields:
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

        plugin_infos = validate_plugin_info(adir)
        if len(plugin_infos) == 0 and warn:
            logging.warning("'{}' is not a proper plugin directory.")
            return

        for pi in plugin_infos:
            logging.debug("  got plugin info {}".format(pi))
            yield pi


def validate_plugin_info(adir):
    """Check a directory whether it conforms plugin rules.

    Rule:
      It is a valid plugin directory, if it has files with swak plugin module
        style name, it is:

      starts with prefix(`i`, `p`, `m`, `b`, `o`) + '_' + module name
          (snake case).
        ex) i_fake_data.py

    Args:
        adir: Absolute directory path to test.

    Returns:
        list: List of PluginInfo. if this directory does not have one,
            it will be empty.
    """
    pis = []
    if 'memory' in adir:
        pass
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
            if pclass is None:
                # has invalid class, break immediately to report
                break
            cname = pclass.__name__
            pname = '{}.{}'.format(pr, cname.lower())
            dname = os.path.basename(adir)
            cname = "{}.{}".format(pname, cname)
            pi = PluginInfo(fname, pname, dname, cname, mod.main.help, mod)
            pis.append(pi)

    if len(pis) == 0:
        logging.error("{} is not valid plugin directory".format(adir))
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
    logging.error("Can not infer class instance - module {} prefix {} "
                  "filename {}".format(mod, pr, fname))


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
        formatter = StdoutFormatter()
        abuffer = MemoryBuffer(self, False, 1, 1)
        super(DummyOutput, self).__init__(formatter, abuffer)
        self.bulks = []
        self.echo = echo

    def _write(self, bulk):
        """Write a bulk.

        Args:
            bulk (bytearray or list): If the chunk that passes the argument is
              a binary type, bulk is an array of bytes, otherwise it is a list
              of strings.
        """
        if type(bulk) is list:
            if self.echo:
                for line in bulk:
                    print(line)
            self.bulks += bulk
        else:
            if self.echo:
                print(bulk)
            self.bulks.append(bulk)

    def reset(self):
        """Reset events."""
        self.bulks = []


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
    plugin_dir = os.path.join(base_dir, '{}_{}'.format(PLUGINDIR_PREFIX,
                                                       file_name))
    os.mkdir(plugin_dir)

    def base_input_prefix(prefix):
        return 'i' if prefix in ['it', 'ir'] else prefix

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
        code = tpl.render(plugin_prefix=PLUGINDIR_PREFIX,
                          class_name=class_name, type_name=typen,
                          base_name=basen, file_name=file_name)
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


def create_plugin_by_name(plugin_name, args):
    """Create a plugin by name and arguments.

    Args:
        plugin_name (str): Plugin full name
        args (list): Command arguments to instantiate plugin object.

    Returns:
        Plugin module
    """
    for i in range(2):
        import_plugins_package(i == 0)
        try:
            elms = plugin_name.split('.')
            package_name = '.'.join(elms[1:])
            module_name = get_plugin_module_name(plugin_name)
            tn = 'std' if i == 0 else ''
            path = '{}plugins.{}.{}'.format(tn, package_name, module_name)
            __import__(path)
        except ImportError:
            if i == 0:
                pass  # for external plugins
            else:
                raise ValueError("There is no plugin '{}'".
                                 format(plugin_name))
        else:
            mod = sys.modules[path]
            return mod.main(args=args, standalone_mode=False)
