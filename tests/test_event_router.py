"""Test event router."""
import time

import pytest

from swak.event_router import EventRouter
from swak.plugin import DummyOutput
from swak.plugins.filter.mod_filter import Filter


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
    pline = router.match_cache['a.b.c']
    pholder = pline.placeholders
    assert pholder['tag'] == 'a.b.c'
    assert pholder['tag_parts'] == ['a', 'b', 'c']
    assert pholder['tag_prefix'] == ['a', 'a.b', 'a.b.c']
    assert pholder['tag_suffix'] == ['c', 'b.c', 'a.b.c']


def test_event_router(def_output, filter, output):
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
