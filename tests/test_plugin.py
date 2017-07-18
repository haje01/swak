from __future__ import absolute_import

import os
from subprocess import call
from io import StringIO

from swak.config import get_exe_dir
from swak.plugin import enumerate_plugins, get_plugins_dir, dump_plugins_import,\
    calc_plugins_hash, remove_plugins_initpy, check_plugins_initpy,\
    get_plugins_initpy_path
from swak.util import test_logconfig


test_logconfig()


def plugin_filter(_dir):
    return _dir in ['counter', 'stdout']


def plugin_filter1(_dir):
    return _dir in ['counter']


def test_plugin_cmd(capfd):
    remove_plugins_initpy()

    cmd = ['swak', '-vvv', 'list']
    call(cmd)
    out, err = capfd.readouterr()
    assert err == ''
    assert 'Swak has 2 plugin(s)' in out

    # after first command, plugins/__init__.py shall exist.
    assert os.path.isfile(get_plugins_initpy_path())

    cmd = ['swak', 'desc', 'in.counter']
    call(cmd)
    out, err = capfd.readouterr()
    assert "Emit incremental number" in out

    cmd = ['swak', 'desc', 'in.notexist']
    call(cmd)
    out, err = capfd.readouterr()
    assert "Can not find" in err


def test_plugin_util():
    path = os.path.join(get_exe_dir(), 'plugins')
    assert path == get_plugins_dir()

    plugin_infos = list(enumerate_plugins(None, plugin_filter))
    assert len(plugin_infos) > 0


def test_plugin_dump():
    dump = """\
# WARNING: Auto-generated code. Do not edit.

from __future__ import absolute_import

from swak.plugins.counter import in_counter
from swak.plugins.stdout import out_stdout

MODULE_MAP = {
    'in.counter': in_counter,
    'out.stdout': out_stdout,
}
"""

    sbuf = StringIO()
    dump_plugins_import(sbuf)
    assert dump == sbuf.getvalue()
    sbuf.close()


def test_plugin_initpy():
    # test plugin checksum
    h = calc_plugins_hash(enumerate_plugins(None, plugin_filter1))
    assert '9d4feaa6af4dd11e31572d6c1896d8b2' == h
    h = calc_plugins_hash(enumerate_plugins(None, plugin_filter))
    assert '7ed9a23f52202cd70253890a591bb96a'

    # test plugins/__init__.py creation
    remove_plugins_initpy()

    # enumerate 1 plugin and __init__.py has been created.
    created, chksum1 = check_plugins_initpy(enumerate_plugins(None,
                                                              plugin_filter1))
    assert created

    # enumerate 1 plugin again and __init__.py hasn't been created.
    created, _ = check_plugins_initpy(enumerate_plugins(None, plugin_filter1))
    assert not created

    # enumerate 2 plugin and __init__.py has been created.
    created, chksum = check_plugins_initpy(enumerate_plugins(None,
                                                            plugin_filter))
    assert created
    assert chksum != chksum1
