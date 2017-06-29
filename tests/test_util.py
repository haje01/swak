"""Test util & config functions."""
import os
import tempfile

import pytest

from swak.config import get_home_cfgpath, CFG_FNAME, _select, select_and_parse
from swak.util import get_home_dir


CFG = """
svc_name: swak-test
svc_dname: "Swak: Multi-Agent Service (Test)"
"""


@pytest.fixture(scope="function")
def test_home():
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

    # shutil.rmtree(test_home)


def test_util_cfg(test_home):
    cpath = get_home_cfgpath()
    cpath = cpath.replace(test_home, '')
    assert CFG_FNAME == cpath.strip(os.sep)

    # select explicit cfg path
    assert '/path/to/expcfg' == _select('/path/to/expcfg', False)

    # select envvar cfg path
    os.environ['SWAK_HOME'] = '/path/to/home'
    cpath = _select(None, False)
    assert '/path/to/home/config.yml' == cpath.replace('\\', '/')

    # prefer explicit cfg path to envvar
    assert '/path/to/expcfg' == _select('/path/to/expcfg', False)

    # select cfg in exe dir if no explict / envvar path exists.
    del os.environ['SWAK_HOME']
    path = os.path.join(get_home_dir(), 'config.yml')
    with open(path, 'wt') as f:
        f.write(CFG)
    assert path == _select(None, False)

    cfg = select_and_parse()
    assert 'swak-test' == cfg['svc_name']
    # check default logger
    assert 'logger' in cfg
    # check resolved param
    assert get_home_dir() in cfg['logger']['handlers']['file']['filename']

    os.unlink(path)
