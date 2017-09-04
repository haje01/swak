"""This module implements plugin test."""

from __future__ import absolute_import

import os
from subprocess import call
from io import StringIO
import shutil

import pytest

from swak.config import get_exe_dir
from swak.plugin import enumerate_plugins, get_plugins_dir,\
    dump_plugins_import, calc_plugins_hash, get_plugins_initpy_path,\
    PREFIX, init_plugins_info
from swak.util import test_logconfig

SWAK_CLI = 'swak.bat' if os.name == 'nt' else 'swak'

test_logconfig()


@pytest.fixture
def init_plugins():
    """Init plugin info."""
    init_plugins_info()


def plugin_filter(_dir):
    """Filter plugins."""
    return _dir in ['counter', 'stdout']


def plugin_filter_ext(_dir):
    """Plugin filter for external plugin test."""
    return _dir in ['testfoo']


def test_plugin_cmd(capfd, init_plugins):
    """Test plugin list & desc command."""
    cmd = [SWAK_CLI, '-vv', 'list']
    try:
        call(cmd)
    except FileNotFoundError:
        return

    out, err = capfd.readouterr()
    print(err)
    assert 'Swak has 4 standard plugins' in out

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


def test_plugin_init_cmd(capfd, init_plugins):
    """Test plugin init command."""
    # remove previous test pacakge.
    base_dir = get_plugins_dir(False)
    plugin_dir = os.path.join(base_dir, 'testfoo')
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
        assert '# swak-testfoo' in text
        assert "plugin package for Swak" in text

    # enumerate external plugins
    plugin_infos = list(enumerate_plugins(False, _filter=plugin_filter_ext))
    assert plugin_infos[0].dname == 'testfoo'

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
    plugin_infos = list(enumerate_plugins(True, None, plugin_filter))
    assert len(plugin_infos) > 0

    # check external plugin dir
    path = os.path.join(get_exe_dir(), 'plugins')
    assert path == get_plugins_dir(False)


def test_plugin_dump():
    """Test plugin information dump."""
    dump = """\
# WARNING: Auto-generated code. Do not edit.

from swak.stdplugins.counter import in_counter
from swak.stdplugins.stdout import out_stdout

MODULE_MAP = {
    'in.counter': in_counter,
    'out.stdout': out_stdout,
}
""".replace('/', os.path.sep)

    sbuf = StringIO()
    dump_plugins_import(True, sbuf, _filter=plugin_filter)
    assert dump == sbuf.getvalue().replace(get_exe_dir(), '')
    sbuf.close()


def test_plugin_initpy():
    """Test plugin __init__.py."""
    # test plugin checksum
    h = calc_plugins_hash(enumerate_plugins(True, plugin_filter))
    assert '94d7a4e72a88639e8a136ea821effcdb' == h
