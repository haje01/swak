"""This module implements plugin test."""
from __future__ import absolute_import

import os
from subprocess import call
import shutil
import types

import pytest

from swak.config import get_exe_dir
from swak.plugin import iter_plugins, get_plugins_dir,\
    get_plugins_initpy_path, PREFIX, import_plugins_package, TextInput,\
    Parser
from swak.util import test_logconfig, which_exe
from swak.const import PLUGIN_PREFIX

SWAK_CLI = 'swak.bat' if os.name == 'nt' else 'swak'

test_logconfig()


def plugin_filter(_dir):
    """Filter plugins."""
    return _dir in ['scounter', 'stdout']


def plugin_filter_ext(_dir):
    """Plugin filter for external plugin test."""
    return _dir in ['{}-testfoo'.format(PLUGIN_PREFIX)]


def test_plugin_cmd(capfd):
    """Test plugin list & desc command."""
    cmd = [SWAK_CLI, '-vv', 'list']
    try:
        call(cmd)
    except FileNotFoundError:
        return

    out, err = capfd.readouterr()
    print(err)
    assert 'standard plugins' in out

    # after first command, plugins/__init__.py shall exist.
    assert os.path.isfile(get_plugins_initpy_path(True))

    cmd = [SWAK_CLI, 'desc', 'in.counter']
    call(cmd)
    out, err = capfd.readouterr()
    assert "Generate incremental numbers" in out

    cmd = [SWAK_CLI, 'desc', 'in.notexist']
    call(cmd)
    out, err = capfd.readouterr()
    assert "Can not find" in err


@pytest.mark.skipif(which_exe('git') is None, reason="requires git")
def test_plugin_clone(capfd):
    """Test clone external plugin."""
    test_plugin = 'swak-plugin-boo'
    base_dir = get_plugins_dir(False)
    clone_dir = os.path.join(base_dir, test_plugin)

    def del_plugin():
        # delete existing test plugin
        if os.path.isdir(clone_dir):
            shutil.rmtree(clone_dir)

    del_plugin()
    git_clone_cmd = ['git', 'clone',
                     'https://github.com/haje01/{}'.format(test_plugin),
                     clone_dir]
    call(git_clone_cmd)
    out, err = capfd.readouterr()
    assert 'Cloning into' in err
    assert os.path.isdir(clone_dir)

    cmd = [SWAK_CLI, 'list']
    call(cmd)
    out, err = capfd.readouterr()
    assert 'out.boo' in out

    del_plugin()


def test_plugin_init_cmd(capfd):
    """Test plugin init command."""
    # remove previous test pacakge.
    base_dir = get_plugins_dir(False)
    plugin_dir = os.path.join(base_dir, '{}-testfoo'.format(PLUGIN_PREFIX))
    if os.path.isdir(plugin_dir):
        shutil.rmtree(plugin_dir)

    cmd = [SWAK_CLI, 'init', '--type', 'in', '--type', 'par', '--type', 'mod',
           '--type', 'buf', '--type', 'out', 'testfoo', 'TestFoo']
    try:
        call(cmd)
    except FileNotFoundError:
        return
    out, err = capfd.readouterr()
    assert err == ''

    for pr in PREFIX:
        pfile = os.path.join(plugin_dir, '{}_testfoo.py'.format(pr))
        assert os.path.isfile(pfile)
        with open(pfile, 'rt') as f:
            code = f.read()
            assert "class TestFoo" in code

    readme_file = os.path.join(plugin_dir, 'README.md')
    assert os.path.isfile(readme_file)
    with open(readme_file, 'rt') as f:
        text = f.read()
        assert '# {}-testfoo'.format(PLUGIN_PREFIX) in text
        assert "plugin package for Swak" in text

    test_file = os.path.join(plugin_dir, 'test_testfoo.py')
    assert os.path.isfile(test_file)
    with open(test_file, 'rt') as f:
        code = f.read()
        assert 'test_testfoo' in code

    # enumerate external plugins
    plugin_infos = list(iter_plugins(False, _filter=plugin_filter_ext))
    assert plugin_infos[0].dname == '{}-testfoo'.format(PLUGIN_PREFIX)

    # desc command should find new external plugins
    cmd = [SWAK_CLI, 'list']
    call(cmd)
    out, err = capfd.readouterr()
    assert 'in.testfoo' in out
    assert 'par.testfoo' in out

    # check duplicate plugin error
    cmd = [SWAK_CLI, 'init', '--type', 'out', 'stdout', 'Stdout']
    call(cmd)
    out, err = capfd.readouterr()
    assert 'already exists' in err

    shutil.rmtree(plugin_dir)

    # check after removing
    cmd = [SWAK_CLI, 'list']
    call(cmd)
    out, err = capfd.readouterr()
    assert err == ''
    assert '0 external plugin' in out


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


def test_plugin_basic(router):
    """Test plugins basic features."""
    class FooInput(TextInput):
        def read_lines(self):
            yield "john 1"
            yield "jane 2"
            yield "smith 3"

    class FooParser(Parser):
        def parse(self, line):
            name, rank = line.split()
            return dict(name=name, rank=rank)

    parser = FooParser()
    parser.set_router(router)
    dtinput = FooInput()
    dtinput.set_router(router)
    dtinput.set_parser(parser)
    dtinput.set_tag("test")

    def filter(line):
        return 'j' in line

    dtinput.set_filter_func(filter)
    dtinput.read()

    events = router.def_output.events['test']
    assert len(events) == 2
    assert events[0][1]['name'] == 'john'
    assert events[1][1]['name'] == 'jane'
