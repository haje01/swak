"""Test reform plugin."""
import socket

import pytest

from swak.plugin import DummyOutput
from swak.event_router import EventRouter

from .mod_reform import Reform


@pytest.fixture()
def def_output():
    """Create default output and returns it."""
    return DummyOutput()


def test_reform(def_output):
    """Test modifier basic."""
    adds = [('k1', 'v1'), ('k2', 'v2')]
    mod = Reform(adds, [])

    # add field
    router = EventRouter(def_output)
    router.add_rule("test", mod)
    router.emit("test", 0, {})
    assert len(def_output.events['test'][0][1]) == 2
    assert 'k1' in def_output.events['test'][0][1]
    assert 'k2' in def_output.events['test'][0][1]

    # delete field
    def_output.reset()
    router = EventRouter(def_output)
    dels = ['k1']
    mod = Reform([], dels)
    router.add_rule("test", mod)
    records = {'k1': 'v1', 'k2': 'v2'}
    router.emit("test", 0, records)
    assert len(def_output.events['test'][0][1]) == 1
    assert 'k1' not in def_output.events['test'][0][1]


def test_reform_expand(def_output):
    """Test expand syntax."""
    adds = {("host", "#{socket.gethostname}")}
    mod = Reform(adds, [])
    router = EventRouter(def_output)
    router.add_rule("test", mod)
    router.emit("test", 0, {})
    hostname = socket.gethostname()
    assert "host" in def_output.events['test'][0][1]
    assert def_output.events['test'][0][1]['host'] == hostname
