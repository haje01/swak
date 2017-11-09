"""This module implements plugin base."""

import os
import sys
import glob
from collections import namedtuple
import logging
import types
import time
from queue import Empty

from swak.config import get_exe_dir
from swak.exception import UnsupportedPython
from swak.const import PLUGINDIR_PREFIX
from swak.formatter import StdoutFormatter
from swak.util import get_plugin_module_name, stop_iter_when_signalled
from swak.data import OneDataStream


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
        logging.info("starting plugin {}".format(self))
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
        logging.info("stopping plugin {}".format(self))
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
        logging.info("shutting down plugin {}".format(self))
        assert not self.started  # Stop first
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
            tag (str): data tag.
        """
        super(Input, self).__init__()
        self.encoding = None
        self.proxy = False

    def read(self, stop_event):
        """Generate data stream.

        This is a function that blocks until all data is exhausted.

        Args:
            stop_event (threading.Event): Stop event

        Yield:
            tuple: (tag, DataStream)
        """
        logging.debug("Input.read")
        for tag, ds in self.generate_stream(self.generate_data, stop_event):
            yield tag, ds

    def generate_data(self):
        """Generate data.

        Yields:
            tuple: time, data
        """
        raise NotImplementedError()

    def generate_stream(self, gen_data, stop_event):
        """Generate data stream from data generator.

        Inefficient default implementation.

        Args:
            gen_data (function): Data generator function.
            stop_event (threading.Event): Stop event

        Yields:
            tuple: (tag, DataStream)
        """
        logging.debug("Input.generate_stream gen_data {}".format(gen_data))
        for utime, data in gen_data(stop_event):
            # Omit blank data that would have been generated under
            #  inappropriate input conditions.
            if len(data) == 0:
                continue
            logging.warning("yield inefficient OneDataStream from {}. "
                            "Implement optimized generate_stream!.".
                            format(self))
            yield self.tag, OneDataStream(utime, data)


class ProxyInput(Input):
    """Input proxy class.

    This class is used in the aggregated thread model.
    """

    def __init__(self):
        """Init."""
        super(ProxyInput, self).__init__()
        self.recv_queues = {}
        self.proxy = True

    def append_recv_queue(self, tag, queue):
        """Append receive queue.

        Args:
            tag (str): data tag.
            queue (Queue): Receiving queue
        """
        assert queue not in self.recv_queues, "The queue has already been "\
            "appended."
        self.recv_queues[tag] = queue

    def generate_stream(self, gen_data, stop_event):
        """Generate data stream from data generator.

        Note: Yield (None, None) tuple if the queue is empty to give agent a
         chance to flush,

        Args:
            gen_data: Data generator.
            stop_event (threading.Event): Stop event.

        Yields:
            tuple: (tag, DataStream)
        """
        while True:
            # Loop each receive queue
            for tag, queue in self.recv_queues.items():
                while True:
                    try:
                        stop_iter_when_signalled(stop_event)
                        ds = queue.get_nowait()
                    except Empty:
                        # Give a chance to flush.
                        yield None, None
                        # Process next queue
                        break
                    else:
                        logging.debug("yield ds")
                        yield tag, ds


class RecordInput(Input):
    """Base class for input plugin which emits record.

    This if usually for a generative input plugin which knows how to genreate
      data and **emit** record directly to the data router. (no following
      parser is needed.)

    Function to be implemented:

        ``generate_record``
    """

    def generate_data(self, stop_event):
        """Generate data by reading lines from the source.

        If explicit encoding, filter & parser exist, apply them.

        Args:
            stop_event (threading.Event): Stop event

        Yields:
            tuple: time, data
        """
        logging.debug("RecordInput.generate_data")
        for record in self.generate_record():
            stop_iter_when_signalled(stop_event)
            yield time.time(), record

    def generate_record(self):
        """Generate records.

        Note: Don't do blocking operation. return an empty dict in inadequate
            situations.

        Yields:
            dict: A record.
        """
        raise NotImplementedError()


class TextInput(Input):
    """Base class for input plugin which reads text and emits line.

    This is usally for a plugin which reads text from source, seperate it by
        lines and **feed** them to the following parser.

    Function to be implemented:

        ``generate_line``
    """

    def __init__(self):
        """Init."""
        super(TextInput, self).__init__()
        self.parser = None
        self.filter_fn = None
        self.encoding = None

    def set_encoding(self, encoding):
        """Set encoding of input source.

        Args:
            encoding (str): Encoding of input source.
        """
        self.encoding = encoding

    def set_parser(self, parser):
        """Set parser for this TextInput plugin."""
        self.parser = parser

    def generate_data(self, stop_event):
        """Generate data by reading lines from the source.

        If explicit encoding, filter & parser exist, apply them.

        Args:
            stop_event (threading.Event): Stop event

        Yields:
            tuple: time, data
        """
        for line in self.generate_line():
            stop_iter_when_signalled(stop_event)

            if stop_event is not None:
                if not stop_event.wait(0.0):
                    raise StopIteration()

            if self.encoding is not None:
                line = line.decode(self.encoding)
            # Test by filter function
            if self.filter_fn is not None:
                if not self.filter_fn(line):
                    continue
            if self.parser is not None:
                data = self.parser.parse(line)
            else:
                data = line
            yield time.time(), data

    def generate_line(self):
        """Generate lines.

        Note: Don't do blocking operation. return an empty string in inadequate
            situations.

        Yields:
            str: A text line.
        """
        raise NotImplementedError()

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

    def prepare_for_stream(self, tag, ds):
        """Prepare to modify data stream.

        Args:
            tag (str): data tag
            ds (datatream): data stream
        """
        pass

    def modify(self, tag, utime, record):
        """Modify data.

        Args:
            tag (str): data tag
            utime (float): data time stamp.
            record (dict): data record

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
        self.proxy = False

    def _shutdown(self):
        """Shut down the plugin."""
        logging.info("Output._shutdown")
        if self.buffer is not None and self.buffer.flush_at_shutdown:
            logging.info("need flushing at shutdown for {} buffer {}".
                         format(self, self.buffer))
            self.flush(True)

    def flush(self, flush_all=False):
        """Flushing buffer.

        Args:
            flush_all (bool): Whether flush all or just one.
        """
        if self.buffer is not None:
            logging.debug("Output.flush")
            self.buffer.flushing(flush_all)

    def set_buffer(self, buffer):
        """Set output bufer."""
        self.buffer = buffer

    def _start(self):
        """Implement start."""
        if self.buffer is not None:
            self.buffer.start()

    def _stop(self):
        """Implement stop."""
        if self.buffer is not None:
            self.buffer.stop()

    def emit_stream(self, tag, ds):
        """Emit data stream to queue or directly to output target.

        Args:
            tag (str): data tag.
            ds (datatream): data stream.

        Returns:
            int: Adding size of the stream.
        """
        logging.debug("Output.emit_stream")
        return self.handle_stream(tag, ds)

    def handle_stream(self, tag, ds):
        """Handle data stream from emit events.

        Format each data and write it to buffer.

        Args:
            tag (str)
            ds (datatream)

        Returns:
            int: Adding size of the stream.
        """
        logging.debug("Output.handle_stream")
        adding_size = 0
        for utime, record in ds:
            dtime = self.formatter.timestamp_to_datetime(utime)
            formatted = self.formatter.format(tag, dtime, record)
            if self.buffer is not None:
                adding_size += self.buffer.append(formatted)
            else:
                self.write(formatted)
        return adding_size

    def write(self, bulk):
        """Write a bulk.

        NOTE: A bulk can have the following types:
        - str: When there is no buffer
        - bytearray: When there is a buffer of binary format
        - list: When there is a buffer of string format

        The output must support various bulk types depending on the presence
         and supported formats of the buffer.

        Args:
            bulk
        """
        if len(bulk) == 0:
            return
        logging.debug("Output.write")
        self._write(bulk)

    def _write(self, bulk):
        """Write a bulk to the output.

        NOTE: A bulk can have the following types:
        - str: When there is no buffer
        - bytearray: When there is a buffer of binary format
        - list: When there is a buffer of string format

        An output plugin must support various bulk types depending on the
         presence and supported formats of the buffer.

        Args:
            bulk
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
        logging.debug("may_flushing")
        if self.buffer is not None:
            self.buffer.may_flushing(last_flush_interval)


class ProxyOutput(Plugin):
    """Output proxy class.

    This class is used in the aggregated thread model.
    """

    def __init__(self, queue):
        """Init.

        Args:
            queue (Queue): Sending queue.
        """
        super(ProxyOutput, self).__init__()
        self.send_queue = queue
        logging.debug("ProxyOutput queue {}".format(queue))
        self.proxy = True

    def emit_stream(self, tag, ds):
        """Emit data stream to inter-thread queue.

        Args:
            tag (str): Data tag.
            ds (datatream): Data stream.
        """
        # Put data stream to the queue, block if necessary.
        st = time.time()
        self.send_queue.put(ds, True)
        latency = time.time() - st
        logging.debug("ProxyOutput.emit_events - queue put latency {:.2f}".
                      format(latency))


def is_kind_of_output(plugin):
    """Return True if given plugin is Output or ProxyOutput."""
    return isinstance(plugin, Output) or isinstance(plugin, ProxyOutput)


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
                # Has invalid class, break immediately to report
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
        logging.info("DummyOutput.__init__")
        formatter = StdoutFormatter()
        super(DummyOutput, self).__init__(formatter, None)
        self.bulks = []
        self.echo = echo

    def _write(self, bulk):
        """Write a bulk to the output.

        NOTE: A bulk can have the following types:
        - str: When there is no buffer
        - bytearray: When there is a buffer of binary format
        - list: When there is a buffer of string format

        An output plugin must support various bulk types depending on the
         presence and supported formats of the buffer.

        Args:
            bulk
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
        prefixds (list): List of plugin prefixes
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

    # Create each type module
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

    # Create README
    readme_file = os.path.join(plugin_dir, 'README.md')
    with open(readme_file, 'wt') as f:
        tpl = env.get_template('tmpl_readme.md')
        code = tpl.render(plugin_prefix=PLUGINDIR_PREFIX,
                          class_name=class_name, type_name=typen,
                          base_name=basen, file_name=file_name)
        f.write(code)

    # Create test file
    test_file = os.path.join(plugin_dir, 'test_{}.py'.format(file_name))
    with open(test_file, 'wt') as f:
        tpl = env.get_template('tmpl_unittest.py')
        typens = [_get_full_name(pr, False) for pr in prefixes]
        prefixes = [base_input_prefix(pr) for pr in prefixes]
        code = tpl.render(class_name=class_name, prefixes=prefixes,
                          type_names=typens, file_name=file_name)
        f.write(code)

    # Create __init__.py
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
                pass  # For external plugins
            else:
                raise ValueError("There is no plugin '{}'".
                                 format(plugin_name))
        else:
            mod = sys.modules[path]
            return mod.main(args=args, standalone_mode=False)
