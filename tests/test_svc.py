"""Test Windows & Unix(Linux, OS X) service."""

import os
from subprocess import Popen
import tempfile
import time
import logging

import pytest
import yaml

from swak.util import is_windows, get_winsvc_status, query_pid_path
from swak.config import select_and_parse

pytestmark = pytest.mark.skipif('SWAK_BUILD' not in os.environ, reason="This"
                                " test is for build mode.")

WSVC_CUR_STATE = 1
WSVC_CMD_BUILD = ['pyinstaller.exe', 'swak/win_svc.py',
                  '--hidden-import=win32timezone', '--onefile']
WSVC_DIST_DIR = os.path.join(os.getcwd(), 'dist')
WSVC_EXE = os.path.join(WSVC_DIST_DIR, 'win_svc.exe')
WSVC_CMD_INSTALL = [WSVC_EXE, 'install']
WSVC_CMD_START = [WSVC_EXE, 'start']
WSVC_CMD_STOP = [WSVC_EXE, 'stop']
WSVC_CMD_REMOVE = [WSVC_EXE, 'remove']

USVC_CMD_START = ['python', '-m', 'swak.unix_svc', 'start']
USVC_CMD_STOP = ['python', '-m', 'swak.unix_svc', 'stop']


CFG = """
svc_name: swak-test
svc_dname: "Swak: Multi-Agent Service (Test)"
"""


@pytest.fixture(scope="function")
def test_home():
    test_home = tempfile.gettempdir()
    cfg_path = os.path.join(test_home, 'config.yml')
    # delete previous cfg file
    if os.path.isfile(cfg_path):
        os.unlink(cfg_path)

    f = open(cfg_path, 'wt')
    f.write(CFG)
    f.close()

    yield test_home

    # shutil.rmtree(test_home)


@pytest.fixture(scope="function")
def unix_svc(test_home):
    cenv = os.environ.copy()
    cenv.update(dict(SWAK_HOME=test_home))

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
@pytest.mark.skipif('APPVEYOR' in os.environ, reason="Can't run PyInstaller in"
                    " AppVeyor")
def win_svc(test_home):
    import win32service

    cenv = os.environ.copy()
    cenv.update(dict(SWAK_HOME=test_home))
    os.environ = cenv
    cfg = select_and_parse()
    svc_name = cfg['svc_name']

    if get_winsvc_status(svc_name) is not None:
        logging.critical("Found previously installed service. Remove it"
                         " first.")
        p = Popen(WSVC_CMD_STOP, env=cenv)
        assert p.returncode is None
        p = Popen(WSVC_CMD_REMOVE, env=cenv)
        time.sleep(3)
        assert p.returncode is None
        time.sleep(3)

    # build
    p = Popen(WSVC_CMD_BUILD, env=cenv)
    assert p.returncode is None

    # install
    p = Popen(WSVC_CMD_INSTALL, env=cenv)
    assert p.returncode is None
    time.sleep(3)
    ret = get_winsvc_status(svc_name)
    assert ret is not None
    assert win32service.SERVICE_STOPPED == ret[WSVC_CUR_STATE]

    # start
    p = Popen(WSVC_CMD_START, env=cenv)
    assert p.returncode is None
    time.sleep(3)
    ret = get_winsvc_status(svc_name)
    if 'APPVEYOR' not in os.environ:
        assert win32service.SERVICE_RUNNING == ret[WSVC_CUR_STATE]

    yield None

    # stop
    p = Popen(WSVC_CMD_STOP, env=cenv)
    assert p.returncode is None
    time.sleep(3)
    ret = get_winsvc_status(svc_name)
    assert win32service.SERVICE_STOPPED == ret[WSVC_CUR_STATE]

    # remove
    p = Popen(WSVC_CMD_REMOVE, env=cenv)
    time.sleep(3)
    assert p.returncode is None
    assert None == get_winsvc_status(svc_name)


@pytest.mark.skipif(is_windows(), reason="requires Unix OS")
def test_svc_unix(unix_svc):
    pass


@pytest.mark.skipif(not is_windows(), reason="requires Windows OS")
def test_svc_windows(win_svc):
    pass
