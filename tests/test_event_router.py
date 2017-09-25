"""This module implements event router test."""
import time

import pytest

from swak.plugin import DummyOutput

from swak.stdplugins.filter.mod_filter import Filter
from swak.stdplugins.reform.mod_reform import Reform


@pytest.fixture()
def filter():
    """Create filter plugin and returns it."""
    return Filter([("k", "V")])


@pytest.fixture()
def output():
    """Create default output and returns it."""
    return DummyOutput()


def test_event_router_pipeline(router):
    """Test event router cache."""
    assert len(router.match_cache) == 0
    router.emit("a.b.c", 0, {"k": "v"})
    assert len(router.match_cache) == 1


def test_event_router_basic(router):
    """Test event router."""
    # router with only default output.
    router.emit("test", time.time(), {"k": "v"})
    assert len(router.def_output.events['test']) == 1


def test_event_router_basic2(router, output):
    """Test router with an output."""
    router.add_rule("test", output)
    router.emit("test", time.time(), {"k": "v"})
    assert len(output.events['test']) == 1


def test_event_router_basic3(router, output, filter):
    """Test router with modifier & output."""
    assert len(output.events['test']) == 0
    router.add_rule("test", filter)
    router.add_rule("test", output)
    router.emit("test", time.time(), {"k": "v"})
    # the record filtered out.
    assert len(output.events['test']) == 0

    # unmatched event goes to default output
    router.emit("foo", time.time(), {"k": "v"})
    assert 'foo' in router.def_output.events
    assert 'foo' not in output.events


def test_event_router_complex(router):
    r"""Test V shaped event router.

    a     b
     \   /
       c
    """
    reform_a = Reform([('a', "1")])
    reform_b = Reform([('b', "2")])
    reform_c = Reform([('c', "3")])

    router.add_rule("a", reform_a)
    router.add_rule("b", reform_b)
    router.add_rule("*", reform_c)

    # Pipeline: a -> c
    router.def_output.reset()
    router.emit("a", 0, {})
    record = router.def_output.events["a"][0][1]
    assert dict(a="1", c="3") == record

    # Pipeline: b -> c
    router.def_output.reset()
    router.emit("b", 0, {})
    record = router.def_output.events["b"][0][1]
    assert dict(b="2", c="3") == record

    # Pipeline: c
    router.def_output.reset()
    router.emit("c", 0, {})
    record = router.def_output.events["c"][0][1]
    assert dict(c="3") == record

    # Check generated pipeline structure
    assert {'a', 'b', 'c'} == set(router.match_cache.keys())
    assert len(router.match_cache['a'].modifiers) == 2
    assert len(router.match_cache['b'].modifiers) == 2
    assert len(router.match_cache['c'].modifiers) == 1
