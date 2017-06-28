"""Test Windows & Unix(Linux, OS X) service."""

import os
from subprocess import Popen
import tempfile
import time

import pytest
import yaml

from swak.util import is_windows, get_winsvc_status, query_pid_path
from swak.config import select_and_parse

WSVC_CUR_STATE = 1
WSVC_CMD_INSTALL = ['python', '-m', 'swak.win_svc', 'install']
WSVC_CMD_START = ['python', '-m', 'swak.win_svc', 'start']
WSVC_CMD_STOP = ['python', '-m', 'swak.win_svc', 'stop']
WSVC_CMD_REMOVE = ['python', '-m', 'swak.win_svc', 'remove']

USVC_CMD_START = ['python', '-m', 'swak.unix_svc', 'start']
USVC_CMD_STOP = ['python', '-m', 'swak.unix_svc', 'stop']


CFG = """
svc_name: swak-test
svc_dname: "Multi-purpose Agent Platform (Test)"
"""

SVC_WAIT_SEC = 5


@pytest.fixture(scope="function")
def test_cfg():
    cfg_path = os.path.join(tempfile.gettempdir(), 'cfg-test.yml')
    # delete previous cfg file
    if os.path.isfile(cfg_path):
        os.unlink(cfg_path)

    f = open(cfg_path, 'wt')
    f.write(CFG)
    f.close()

    yield cfg_path

    # os.unlink(cfg_path)


@pytest.fixture(scope="function")
def unix_svc(test_cfg):
    cenv = os.environ.copy()
    cenv.update(dict(SWAK_CFG=test_cfg))

    cfg = yaml.load(CFG)
    svc_name = cfg['svc_name']
    pid_path = query_pid_path(svc_name)

    # remove previous pid
    if os.path.isfile(pid_path):
        Popen(USVC_CMD_STOP, env=cenv)

    p = Popen(USVC_CMD_START, env=cenv)
    assert p.returncode is None
    time.sleep(2)
    assert os.path.isfile(pid_path)

    yield None

    p = Popen(USVC_CMD_STOP, env=cenv)
    assert p.returncode is None
    time.sleep(1)
    assert not os.path.isfile(pid_path)


@pytest.fixture(scope="function")
def win_svc(test_cfg):
    import win32service

    cenv = os.environ.copy()
    cenv.update(dict(SWAK_CFG=test_cfg))
    os.environ = cenv
    cfg = select_and_parse()
    svc_name = cfg['svc_name']

    if get_winsvc_status(svc_name) is not None:
        Popen(WSVC_CMD_REMOVE, env=cenv)
        time.sleep(SVC_WAIT_SEC)

    p = Popen(WSVC_CMD_INSTALL, env=cenv)
    assert p.returncode is None
    time.sleep(SVC_WAIT_SEC)
    ret = get_winsvc_status(svc_name)
    assert win32service.SERVICE_STOPPED == ret[WSVC_CUR_STATE]

    p = Popen(WSVC_CMD_START, env=cenv)
    assert p.returncode is None
    time.sleep(SVC_WAIT_SEC)
    ret = get_winsvc_status(svc_name)
    assert win32service.SERVICE_RUNNING == ret[WSVC_CUR_STATE]

    yield None

    p = Popen(WSVC_CMD_STOP, env=cenv)
    assert p.returncode is None
    time.sleep(SVC_WAIT_SEC)
    assert win32service.SERVICE_STOPPED == ret[WSVC_CUR_STATE]

    p = Popen(WSVC_CMD_REMOVE, env=cenv)
    time.sleep(SVC_WAIT_SEC)
    assert p.returncode is None
    assert None == get_winsvc_status(svc_name)


@pytest.mark.skipif(is_windows(), reason="requires Unix OS")
def test_svc_unix(unix_svc):
    pass


@pytest.mark.skipif(not is_windows(), reason="requires Windows OS")
def test_svc_windows(win_svc):
    pass
