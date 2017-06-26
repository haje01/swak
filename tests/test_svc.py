from subprocess import call

import pytest

from swak.util import is_unix


@pytest.fixture(scope="function")
def unix_svc():
    assert 0 == call(['python', '-m', 'swak.unix_svc', 'start'])
    yield None
    assert 0 == call(['python', '-m', 'swak.unix_svc', 'stop'])


@pytest.mark.skipif(not is_unix(), reason="requires Unix OS")
def test_unix(unix_svc):
    print('hello')


@pytest.mark.skipif(is_unix(), reason="requires Windows OS")
def test_windows():
    print('hello')
