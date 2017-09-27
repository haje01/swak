"""This module implements utility test."""

from __future__ import absolute_import

import os
import sys
import tempfile
import logging

import pytest

from swak.config import CFG_FNAME, select_home, select_and_parse,\
    get_config_path, get_exe_dir
from swak.util import init_home, get_plugin_module_name, update_dict,\
    check_python_version, set_log_verbosity, _verbosity_from_log_level,\
    which_exe, size_value, time_value


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

    d1 = dict(a=1, b=2, d=dict(A=1, B=3))
    d2 = dict(b=3, c=4, d=dict(A=2))
    rv = update_dict(d1, d2)
    assert rv == dict(a=1, b=3, c=4, d=dict(A=2, B=3))

    vi = sys.version_info
    rv = check_python_version()
    assert rv == vi.major

    logger = logging.getLogger()
    org_level = logger.getEffectiveLevel()
    org_verbosity = _verbosity_from_log_level(org_level)
    set_log_verbosity(0)
    new_level = logger.getEffectiveLevel()
    assert new_level == 40
    set_log_verbosity(org_verbosity)

    assert which_exe('date') is not None


def test_util_value():
    """Test size & time value conversion."""
    assert None is size_value(None)
    assert 1 == size_value('1')
    assert 1024 == size_value('1k')
    assert 1024 == size_value('1K')
    assert 1024 ** 2 == size_value('1m')
    assert 1024 ** 2 == size_value('1M')
    assert 1024 ** 3 == size_value('1g')
    assert 1024 ** 3 == size_value('1G')
    assert 1024 ** 4 == size_value('1t')
    assert 1024 ** 4 == size_value('1T')
    with pytest.raises(ValueError):
        size_value('asdf')

    assert None is size_value(None)
    assert 1 == time_value('1')
    assert 1.1 == time_value('1.1')
    assert 1 == time_value('1s')
    assert 1 == time_value('1S')
    assert 60 == time_value('1m')
    assert 60 == time_value('1M')
    assert 60 * 60 == time_value('1h')
    assert 60 * 60 == time_value('1H')
    assert 60 * 60 * 24 == time_value('1d')
    assert 60 * 60 * 24 == time_value('1D')
    with pytest.raises(ValueError):
        size_value('asdf')
