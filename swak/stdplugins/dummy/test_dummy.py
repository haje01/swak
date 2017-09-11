"""Test Dummy plugin."""

from .in_dummy import Dummy


def test_dummy_basic(router):
    """Test basic features of Dummy plugin."""
    record = dict(name="john", score=123)
    dummy = Dummy(record, 3)
    dummy.set_router(router)
    dummy.set_tag("test")

    router.add_rule("test", dummy)
    dummy.read()
    events = router.def_output.events['test']
    assert len(events) == 3
    assert events[0][1]['name'] == 'john'
