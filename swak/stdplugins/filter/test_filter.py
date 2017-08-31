"""Test filter plugin."""

import pytest

from swak.event_router import EventRouter
from swak.plugin import DummyOutput

from .mod_filter import Filter


@pytest.fixture()
def def_output():
    """Create default output and returns it."""
    return DummyOutput()


def init_event_router(doutput, modifiers):
    """Make new event router."""
    doutput.reset()
    router = EventRouter(doutput)
    for modifier in modifiers:
        router.add_rule("test", modifier)
    return router


def emit_records(router):
    """Emit records to router."""
    records = [
        {"k1": "a", "k2": "A"},
        {"k1": "b", "k2": "B"},
        {"k1": "c", "k2": "C"},
        {"k1": "d", "k2": "D"},
    ]
    for i, rec in enumerate(records):
        router.emit("test", i, rec)


def emit_to_new_router(doutput, modifiers):
    """Make new router and emit record to it."""
    router = init_event_router(doutput, modifiers)
    emit_records(router)


def test_filter_basic(def_output):
    """Test filter basic."""
    # test include
    includes = [("k1", "a")]
    filter = Filter(includes)
    emit_to_new_router(def_output, [filter])
    assert len(def_output.events['test']) == 1

    # test include with regexp or
    includes = [("k1", "a|c")]
    filter = Filter(includes)
    emit_to_new_router(def_output, [filter])
    assert len(def_output.events['test']) == 2

    # test include override
    includes = [("k1", "a"), ("k1", "c")]  # k1 == c is effecitve
    filter = Filter(includes)
    emit_to_new_router(def_output, [filter])
    assert len(def_output.events['test']) == 1

    # test multiple includes (multiple includes -> AND)
    includes = [("k1", "a"), ("k2", "B")]
    filter = Filter(includes)
    emit_to_new_router(def_output, [filter])
    assert len(def_output.events['test']) == 0

    includes = [("k1", "a"), ("k2", "A")]
    filter = Filter(includes)
    emit_to_new_router(def_output, [filter])
    assert len(def_output.events['test']) == 1

    # test exclude
    excludes = [("k1", "c")]
    filter = Filter([], excludes)
    emit_to_new_router(def_output, [filter])
    assert len(def_output.events['test']) == 3

    # multiple excludes -> OR
    excludes = [("k1", "c"), ("k2", "C")]
    filter = Filter([], excludes)
    emit_to_new_router(def_output, [filter])
    assert len(def_output.events['test']) == 3

    excludes = [("k1", "c"), ("k2", "B")]
    filter = Filter([], excludes)
    emit_to_new_router(def_output, [filter])
    assert len(def_output.events['test']) == 2

    # test include & exclude conflict
    includes = [("k1", "a|c")]
    excludes = [("k1", "c")]
    filter = Filter(includes, excludes)
    emit_to_new_router(def_output, [filter])
    assert len(def_output.events['test']) == 1
