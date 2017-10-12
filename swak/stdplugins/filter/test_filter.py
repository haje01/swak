"""Test filter plugin."""

from swak.event_router import EventRouter
from swak.plugin import DummyOutput

from .mod_filter import Filter


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


def emit_to_new_router(modifiers):
    """Make new router and emit record to it."""
    doutput = DummyOutput()
    router = init_event_router(doutput, modifiers)
    emit_records(router)
    router.flush()
    return doutput


def test_filter_basic():
    """Test basic features of filter plugin."""
    # test include
    includes = [("k1", "a")]
    filter = Filter(includes)
    def_output = emit_to_new_router([filter])
    assert len(def_output.bulks) == 1

    # test include with regexp or
    includes = [("k1", "a|c")]
    filter = Filter(includes)
    def_output = emit_to_new_router([filter])
    assert len(def_output.bulks) == 2

    # test include override
    includes = [("k1", "a"), ("k1", "c")]  # k1 == c is effecitve
    filter = Filter(includes)
    def_output = emit_to_new_router([filter])
    assert len(def_output.bulks) == 1

    includes = [("k1", "a"), ("k2", "A")]
    filter = Filter(includes)
    def_output = emit_to_new_router([filter])
    assert len(def_output.bulks) == 1

    # test exclude
    excludes = [("k1", "c")]
    filter = Filter([], excludes)
    def_output = emit_to_new_router([filter])
    assert len(def_output.bulks) == 3

    # multiple excludes -> OR
    excludes = [("k1", "c"), ("k2", "C")]
    filter = Filter([], excludes)
    def_output = emit_to_new_router([filter])
    assert len(def_output.bulks) == 3

    excludes = [("k1", "c"), ("k2", "B")]
    filter = Filter([], excludes)
    def_output = emit_to_new_router([filter])
    assert len(def_output.bulks) == 2

    # test include & exclude conflict
    includes = [("k1", "a|c")]
    excludes = [("k1", "c")]
    filter = Filter(includes, excludes)
    def_output = emit_to_new_router([filter])
    assert len(def_output.bulks) == 1
