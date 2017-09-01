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
    remove_plugins_initpy, check_plugins_initpy
from swak.util import test_logconfig

SWAK_CLI = 'swak.bat' if os.name == 'nt' else 'swak'

test_logconfig()


def plugin_filter(_dir):
    """Filter plugins."""
    return _dir in ['counter', 'stdout']


def plugin_filter1(_dir):
    """Filter plugins."""
    return _dir in ['counter']


def test_plugin_cmd(capfd):
    """Test plugin list & desc command."""
    cmd = [SWAK_CLI, '-vv', 'list']
    try:
        call(cmd)
    except FileNotFoundError:
        return

    out, err = capfd.readouterr()
    print(err)
    assert 'Swak has 4 plugins' in out

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


def test_plugin_init_cmd(capfd):
    """Test plugin init command."""
    # remove previous test pacakge.
    base_dir = get_plugins_dir(False)
    plugin_dir = os.path.join(base_dir, 'testfoo')
    if os.path.isdir(plugin_dir):
        shutil.rmtree(plugin_dir)

    cmd = [SWAK_CLI, 'init', '--type', 'in', '--type', 'par', 'testfoo',
           'TestFoo']
    try:
        call(cmd)
    except FileNotFoundError:
        return
    out, err = capfd.readouterr()
    assert err == ''

    input_file = os.path.join(plugin_dir, 'in_testfoo.py')
    assert os.path.isfile(input_file)
    with open(input_file, 'rt') as f:
        code = f.read()
        assert "class TestFoo(BaseInput)" in code

    parser_file = os.path.join(plugin_dir, 'par_testfoo.py')
    assert os.path.isfile(parser_file)
    with open(parser_file, 'rt') as f:
        code = f.read()
        assert "class TestFoo(BaseParser)" in code

    readme_file = os.path.join(plugin_dir, 'README.md')
    assert os.path.isfile(readme_file)
    with open(readme_file, 'rt') as f:
        text = f.read()
        assert '# swak-testfoo' in text
        assert "plugin package for Swak" in text

    shutil.rmtree(plugin_dir)


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
    dump_plugins_import(sbuf, _filter=plugin_filter)
    assert dump == sbuf.getvalue().replace(get_exe_dir(), '')
    sbuf.close()


@pytest.mark.skip(reason="Cause false import of plugins/__init__.py to other"
                  " tests.")
def test_plugin_initpy():
    """Test plugin __init__.py."""
    # test plugin checksum
    h = calc_plugins_hash(enumerate_plugins(None, plugin_filter1))
    assert '9d4feaa6af4dd11e31572d6c1896d8b2' == h
    h = calc_plugins_hash(enumerate_plugins(None, plugin_filter))
    assert '7ed9a23f52202cd70253890a591bb96a'

    # test plugins/__init__.py creation
    remove_plugins_initpy(True)

    # enumerate 1 plugin and __init__.py has been created.
    created, chksum1 = check_plugins_initpy(True,
                                            enumerate_plugins(True, None,
                                                              plugin_filter1))
    assert created

    # enumerate 1 plugin again and __init__.py hasn't been created.
    created, _ = check_plugins_initpy(True,
                                      enumerate_plugins(True, None,
                                                        plugin_filter1))
    assert not created

    # enumerate 2 plugin and __init__.py has been created.
    created, chksum = check_plugins_initpy(True,
                                           enumerate_plugins(True, None,
                                                             plugin_filter))
    assert created
    assert chksum != chksum1
