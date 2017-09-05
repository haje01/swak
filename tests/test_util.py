"""This module implements utility test."""

from __future__ import absolute_import

import os
import tempfile

import pytest

from swak.config import CFG_FNAME, select_home, select_and_parse,\
    get_config_path, get_exe_dir
from swak.util import init_home, get_plugin_module_name


CFG = """
svc_name: swak-test
svc_dname: "Swak: Multi-Agent Service (Test)"
"""


@pytest.fixture(scope="function")
def test_home():
    """Test swak home utilities."""
    old_home = os.environ.get('SWAK_HOME')

    test_home = tempfile.gettempdir()
    os.environ['SWAK_HOME'] = test_home
    cfg_path = os.path.join(test_home, 'config.yml')
    # delete previous cfg file
    if os.path.isfile(cfg_path):
        os.unlink(cfg_path)

    f = open(cfg_path, 'wt')
    f.write(CFG)
    f.close()

    yield test_home

    if old_home is not None:
        os.environ['SWAK_HOME'] = old_home
    # shutil.rmtree(test_home)


def test_util_cfg(test_home):
    """Test config utilities."""
    home = select_home(test_home)
    cpath = get_config_path()
    assert CFG_FNAME in cpath.replace(home, '').strip(os.sep)

    # select explicit home
    assert '/path/to/expcfg' == select_home('/path/to/expcfg', False)

    # select envvar home
    os.environ['SWAK_HOME'] = '/path/to/home'
    home = select_home(None, False)
    assert '/path/to/home' == home

    # prefer explicit home to envvar
    assert '/path/to/home2' == select_home('/path/to/home2', False)

    # select home as exe dir if no explict / envvar home exists.
    del os.environ['SWAK_HOME']
    path = os.path.join(get_exe_dir(), 'config.yml')
    with open(path, 'wt') as f:
        f.write(CFG)
    assert get_exe_dir() == select_home(None, False)

    # test select and parse
    home, cfg = select_and_parse()
    assert get_exe_dir() == home
    assert 'swak-test' == cfg['svc_name']
    # check default logger
    assert 'logger' in cfg
    # check environment variable resolution
    assert home in cfg['logger']['handlers']['file']['filename']

    # select home and parse config
    home, cfg = select_and_parse(test_home)
    init_home(home, cfg)

    os.unlink(path)


def test_util_etc():
    """Test small utilities."""
    assert 'out_stdout.2' == get_plugin_module_name('out.stdout.2')
