"""Test util & config functions."""
import os
import tempfile

import pytest

from swak.config import get_execfg_path, CFG_FNAME, _select, select_and_parse
from swak.util import get_exedir


CFG = """
svcname: swak_test
"""


@pytest.fixture(scope="function")
def test_cfg():
    tmp = tempfile.NamedTemporaryFile(mode='wt', delete=False)
    tmp.write(CFG)
    tmp.close()

    yield tmp.name

    os.unlink(tmp.name)


def test_util_cfg(test_cfg):
    cpath = get_execfg_path()
    cpath = cpath.replace(get_exedir(), '')
    assert CFG_FNAME == cpath.strip(os.sep)


    # select explicit cfg path
    assert '/path/to/expcfg' == _select('/path/to/expcfg')

    # select envvar cfg path
    os.environ['SWAK_CFG'] = '/path/to/envcfg'
    cpath = _select()
    assert '/path/to/envcfg' == cpath

    # prefer explicit cfg path to envvar
    assert '/path/to/expcfg' == _select('/path/to/expcfg')

    # select cfg path within exe dir if no explict / envvar path exists.
    del os.environ['SWAK_CFG']
    path = os.path.join(get_exedir(), 'config.yml')
    with open(path, 'wt') as f:
        assert path == _select()
        pass

    # parse exe dir
    path = os.path.join(get_exedir(), 'config.yml')
    with open(path, 'wt') as f:
        f.write(CFG)

    cfg = select_and_parse()
    assert  'swak_test' == cfg['svcname']

    os.unlink(path)