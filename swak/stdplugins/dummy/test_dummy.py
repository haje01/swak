"""Test Dummy plugin."""

from .i_dummy import Dummy


def test_dummy_basic(router):
    """Test basic features of Dummy plugin."""
    record = dict(name="john", score=123)
    dummy = Dummy(record, 3)
    dummy.set_router(router)
    dummy.set_tag("test")

    router.add_rule("test", dummy)
    router.start()
    assert dummy.started
    dummy.read()
    router.flush()
    bulks = router.def_output.bulks
    assert len(bulks) == 3
    assert 'john' in bulks[0]
