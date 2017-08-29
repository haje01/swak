"""Test event router."""
import time

import pytest

from swak.event_router import EventRouter
from swak.plugin import DummyOutput
from swak.plugins.filter.mod_filter import Filter
from swak.plugins.reform.mod_reform import Reform


@pytest.fixture()
def def_output():
    """Create default output and returns it."""
    return DummyOutput()


@pytest.fixture()
def filter():
    """Create filter plugin and returns it."""
    return Filter([("k", "V")])


@pytest.fixture()
def output():
    """Create default output and returns it."""
    return DummyOutput()


def test_event_router_pipeline(def_output):
    """Test event router cache."""
    router = EventRouter(def_output)
    assert len(router.match_cache) == 0
    router.emit("a.b.c", 0, {"k": "v"})
    assert len(router.match_cache) == 1


def test_event_router_basic(def_output, filter, output):
    """Test event router."""
    # router with only default output.
    router = EventRouter(def_output)
    router.emit("test", time.time(), {"k": "v"})
    assert len(def_output.events['test']) == 1

    # router with an output
    def_output.reset()
    router = EventRouter(def_output)
    router.add_rule("test", output)
    router.emit("test", time.time(), {"k": "v"})
    assert len(output.events['test']) == 1

    # router with modifier & output.
    output.reset()
    assert len(output.events['test']) == 0
    router = EventRouter(def_output)
    router.add_rule("test", filter)
    router.add_rule("test", output)
    router.emit("test", time.time(), {"k": "v"})
    assert len(output.events['test']) == 0


def test_event_router_complex(def_output):
    """Test V shaped event router.
        a     b
         \   /
           c
    """
    reform_a = Reform([('a', "1")])
    reform_b = Reform([('b', "2")])
    reform_c = Reform([('c', "3")])
    router = EventRouter(def_output)
    router.add_rule("a", reform_a)
    router.add_rule("b", reform_b)
    router.add_rule("*", reform_c)

    # Pipeline: a -> c
    def_output.reset()
    router.emit("a", 0, {})
    record = def_output.events["a"][0][1]
    assert dict(a="1", c="3") == record

    # Pipeline: b -> c
    def_output.reset()
    router.emit("b", 0, {})
    record = def_output.events["b"][0][1]
    assert dict(b="2", c="3") == record

    # Pipeline: c
    def_output.reset()
    router.emit("c", 0, {})
    record = def_output.events["c"][0][1]
    assert dict(c="3") == record
