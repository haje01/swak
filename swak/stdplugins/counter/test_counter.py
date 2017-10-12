"""Test counter plugin."""

from .i_counter import Counter


def test_counter_basic(router):
    """Test basic features of counter plugin."""
    counter = Counter(3, 1, 0)
    counter.set_router(router)
    counter.set_tag("test")

    router.add_rule("test", counter)
    router.start()
    assert counter.started
    counter.read()
    router.flush()
    assert len(router.def_output.bulks) == 3
