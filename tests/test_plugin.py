"""This module implements plugin test."""
from __future__ import absolute_import

import os
import types

from swak.config import get_exe_dir
from swak.plugin import iter_plugins, import_plugins_package, TextInput,\
    Parser, get_plugins_dir, Output
from swak.util import test_logconfig
from swak.const import PLUGINDIR_PREFIX
from swak.exception import NoMoreData
from swak.buffer import MemoryBuffer


test_logconfig()


def plugin_filter(_dir):
    """Filter plugins."""
    return _dir in ['scounter', 'stdout']


def plugin_filter_ext(_dir):
    """Plugin filter for external plugin test."""
    return _dir in ['{}-testfoo'.format(PLUGINDIR_PREFIX)]


def test_plugin_util():
    """Test plugin util."""
    # check standard plugin dir
    path = os.path.join(get_exe_dir(), 'stdplugins')
    assert path == get_plugins_dir(True)
    plugin_infos = list(iter_plugins(True, None, plugin_filter))
    assert len(plugin_infos) > 0

    # check external plugin dir
    path = os.path.join(get_exe_dir(), 'plugins')
    assert path == get_plugins_dir(False)


def test_plugin_import():
    """Test import plugins from plugins base package."""
    stdplugins = import_plugins_package(True)
    assert isinstance(stdplugins, types.ModuleType)
    __import__('stdplugins.counter')
    __import__('stdplugins.filter')


def test_plugin_basic(agent):
    """Test plugins basic features."""
    class FooInput(TextInput):
        def __init__(self):
            super(FooInput, self).__init__()
            self.count = 0

        def read_line(self):
            self.count += 1
            if self.count == 1:
                return "john 1"
            elif self.count == 2:
                return "jane 2"
            elif self.count == 3:
                return "smith 3"
            else:
                raise NoMoreData()

    class FooParser(Parser):
        def parse(self, line):
            name, rank = line.split()
            return dict(name=name, rank=rank)

    parser = FooParser()
    dtinput = FooInput()
    dtinput.set_parser(parser)
    agent.register_plugin("test", dtinput)

    def filter(line):
        return 'j' in line

    dtinput.set_filter_func(filter)
    agent.simple_process(dtinput, 0.0)

    bulks = agent.def_output.bulks
    assert len(bulks) == 2
    assert "'name': 'john'" in bulks[0].split('\t')[2]
    assert "'name': 'jane'" in bulks[1].split('\t')[2]


def test_plugin_output():
    """Test output plugin."""
    # stopping output let its buffer stopped.
    buf = MemoryBuffer(None, False)
    out = Output(None, buf)
    assert out.buffer is buf
    out.start()
    assert out.buffer.started
    out.stop()
    assert not out.buffer.started
