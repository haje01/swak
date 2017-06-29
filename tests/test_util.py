"""Test util & config functions."""
import os
import tempfile

import pytest

from swak.config import get_home_cfgpath, CFG_FNAME, _select, select_and_parse
from swak.util import get_home_dir


CFG = """
svc_name: swak-dev
svc_dname: "Multi-purpose Agent Platform (Test)"
"""


@pytest.fixture(scope="function")
def test_cfg():
    tmp = tempfile.NamedTemporaryFile(mode='wt', delete=False)
    tmp.write(CFG)
    tmp.close()

    yield tmp.name

    os.unlink(tmp.name)


def test_util_cfg(test_cfg):
    cpath = get_home_cfgpath()
    cpath = cpath.replace(get_home_dir(), '')
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
    assert 'swak-dev' == cfg['svc_name']
    # check default logger
    assert 'logger' in cfg
    # check resolved param
    assert get_home_dir() in cfg['logger']['handlers']['file']['filename']

    os.unlink(path)
