"""This module implements core module test."""

from __future__ import absolute_import

import os
from subprocess import call
import shutil

import pytest

from swak.plugin import iter_plugins, get_plugins_dir,\
    get_plugins_initpy_path, PREFIX
from swak.util import which_exe
from swak.const import PLUGINDIR_PREFIX
from swak.cli import ptrn_classnm


SWAK_CLI = 'swak.bat' if os.name == 'nt' else 'swak'


@pytest.fixture
def rm_dummies():
    """Remove dummy plugin dirs from previous test."""
    base_dir = get_plugins_dir(False)
    for name in ['testfoo', 'testbad']:
        plugin_dir = os.path.join(base_dir, '{}_{}'.format(PLUGINDIR_PREFIX,
                                                           name))
        if os.path.isdir(plugin_dir):
            shutil.rmtree(plugin_dir)


def plugin_filter_ext(_dir):
    """Plugin filter for external plugin test."""
    return _dir in ['{}_testfoo'.format(PLUGINDIR_PREFIX)]


def test_cli_basic(capfd):
    """Test CLI list & desc commands."""
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

    cmd = [SWAK_CLI, 'desc', 'i.counter']
    call(cmd)
    assert "Generate incremental numbers" in out

    cmd = [SWAK_CLI, 'desc', 'i.notexist']
    call(cmd)
    out, err = capfd.readouterr()
    assert "Can not find" in err

    # desc for sub-command
    cmd = [SWAK_CLI, 'desc', 'o.stdout', '-s', 'f.stdout']
    call(cmd)
    out, err = capfd.readouterr()
    assert '--timezone' in out


@pytest.mark.skipif(which_exe('git') is None, reason="requires git")
def test_cli_clone(capfd):
    """Test clone external plugin."""
    test_plugin = 'swak_plugin_boo'
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
    assert 'o.boo' in out

    del_plugin()


def test_cli_init(capfd, rm_dummies):
    """Test CLI init input(text), parser, modifier and output."""
    # remove previous test pacakge.
    base_dir = get_plugins_dir(False)
    plugin_dir = os.path.join(base_dir, '{}_testfoo'.format(PLUGINDIR_PREFIX))

    # test init plugin with parser & output modules.
    cmd = [SWAK_CLI, 'init', '--type', 'it', '--type', 'p', '--type',
           'm', '--type', 'o', 'testfoo', 'TestFoo']
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
        assert '# {}_testfoo'.format(PLUGINDIR_PREFIX) in text
        assert "plugin package for Swak" in text

    test_file = os.path.join(plugin_dir, 'test_testfoo.py')
    assert os.path.isfile(test_file)
    with open(test_file, 'rt') as f:
        code = f.read()
        assert 'test_testfoo' in code

    # enumerate external plugins
    plugin_infos = list(iter_plugins(False, _filter=plugin_filter_ext))
    assert plugin_infos[0].dname == '{}_testfoo'.format(PLUGINDIR_PREFIX)

    # desc command should find new external plugins
    cmd = [SWAK_CLI, 'list']
    call(cmd)
    out, err = capfd.readouterr()
    assert 'i.testfoo' in out
    assert 'p.testfoo' in out

    # check duplicated plugin error
    cmd = [SWAK_CLI, 'init', '--type', 'o', 'stdout', 'Stdout']
    call(cmd)
    out, err = capfd.readouterr()
    assert 'already exists' in err

    # check duplicate init type error
    cmd = [SWAK_CLI, 'init', '--type', 'it', '--type', 'ir', 'boo',
           'Boo']
    call(cmd)
    out, err = capfd.readouterr()
    assert 'are mutually exclusive' in err

    shutil.rmtree(plugin_dir)

    # check after removing
    cmd = [SWAK_CLI, 'list']
    call(cmd)
    out, err = capfd.readouterr()
    assert err == ''
    assert '0 external plugin' in out


def test_cli_init2(capfd, rm_dummies):
    """Test CLI init input(record) and unsuitable plugin dictory."""
    # remove previous test pacakge.
    base_dir = get_plugins_dir(False)
    plugin_dir = os.path.join(base_dir, '{}_testfoo'.format(PLUGINDIR_PREFIX))

    # test init plugin with parser & output modules.
    cmd = [SWAK_CLI, 'init', '--type', 'ir', 'testfoo', 'TestFoo']
    try:
        call(cmd)
    except FileNotFoundError:
        return
    out, err = capfd.readouterr()
    assert err == ''

    # test illegal names
    cmd = [SWAK_CLI, 'init', '--type', 'ir', 'o_testboo', 'TestBoo']
    call(cmd)
    out, err = capfd.readouterr()

    # desc command should find new external plugins
    cmd = [SWAK_CLI, 'list']
    call(cmd)
    out, err = capfd.readouterr()
    assert 'i.testfoo' in out
    shutil.rmtree(plugin_dir)

    # test warning unsuitable directory
    plugin_dir = os.path.join(base_dir, '{}_testbad'.format(PLUGINDIR_PREFIX))
    if os.path.isdir(plugin_dir):
        shutil.rmtree(plugin_dir)
    os.mkdir(plugin_dir)
    cmd = [SWAK_CLI, 'list']
    call(cmd)
    out, err = capfd.readouterr()
    # should report unsuitable directories
    assert 'is not valid plugin directory' in err

    shutil.rmtree(plugin_dir)


def test_cli_init_names():
    """Test CLI init command names."""
    assert ptrn_classnm.match("Foo") is not None
    assert ptrn_classnm.match("FooCls") is not None
    assert ptrn_classnm.match("FooCls9") is not None
    assert ptrn_classnm.match("Foo_Cls") is not None
    assert ptrn_classnm.match("Foo_Cls9") is not None
    assert ptrn_classnm.match("9Cls") is None
    assert ptrn_classnm.match("_Cls") is None
    assert ptrn_classnm.match("fooCls") is None
