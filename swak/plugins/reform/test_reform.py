"""Test reform plugin."""

import socket

import pytest

from swak.plugin import DummyOutput
from swak.event_router import EventRouter

from .mod_reform import Reform, _tag_suffix


@pytest.fixture()
def def_output():
    """Create default output and returns it."""
    return DummyOutput()


def test_event_router_util():
    """Test event router utility."""
    assert ['test'] == _tag_suffix(['test'])


def test_reform_basic(def_output):
    """Test modifier basic."""
    adds = [('k1', 'v1'), ('k2', 'v2')]
    reform = Reform(adds, [])

    # add field
    router = EventRouter(def_output)
    router.add_rule("test", reform)
    router.emit("test", 0, {})
    assert len(def_output.events['test'][0][1]) == 2
    assert 'k1' in def_output.events['test'][0][1]
    assert 'k2' in def_output.events['test'][0][1]

    # delete field
    def_output.reset()
    router = EventRouter(def_output)
    dels = ['k1']
    reform = Reform([], dels)
    router.add_rule("test", reform)
    records = {'k1': 'v1', 'k2': 'v2'}
    router.emit("test", 0, records)
    assert len(def_output.events['test'][0][1]) == 1
    assert 'k1' not in def_output.events['test'][0][1]


def test_reform_expand(def_output):
    """Test expand syntax."""
    # testpipeline placeholder expand
    adds = [
        ("host", "${hostname}"),
        ("addr", "${hostaddr}"),
        ("firsttag", "${tag_parts[0]}"),
        ("lasttag", "${tag_parts[-1]}"),
        ("first2addr", "${hostaddr_parts[0]}.${hostaddr_parts[1]}"),
        ("last2addr", "${hostaddr_parts[-2]}.${hostaddr_parts[-1]}")
    ]
    reform = Reform(adds, [])
    router = EventRouter(def_output)
    router.add_rule("a.b.c", reform)
    router.emit("a.b.c", 0, {})
    assert "host" in def_output.events['a.b.c'][0][1]
    hostname = socket.gethostname()
    hostaddr = socket.gethostbyname(hostname)
    addr_parts = hostaddr.split('.')
    first2addr = "{}.{}".format(addr_parts[0], addr_parts[1])
    last2addr = "{}.{}".format(addr_parts[-2], addr_parts[-1])
    record = def_output.events['a.b.c'][0][1]
    assert record['host'] == hostname
    assert record['addr'] == hostaddr
    assert record['firsttag'] == 'a'
    assert record['lasttag'] == 'c'
    assert record['first2addr'] == first2addr
    assert record['last2addr'] == last2addr

    # check placeholders
    pholder = reform.placeholders
    assert pholder['tag'] == 'a.b.c'
    assert pholder['tag_parts'] == ['a', 'b', 'c']
    assert pholder['tag_prefix'] == ['a', 'a.b', 'a.b.c']
    assert pholder['tag_suffix'] == ['c', 'b.c', 'a.b.c']
