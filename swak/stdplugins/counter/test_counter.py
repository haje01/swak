"""Test counter plugin."""

from .in_counter import Counter


def test_counter_basic(router):
    """Test basic features of counter plugin."""
    counter = Counter(3, 1, 0)
    counter.set_router(router)
    counter.set_tag("test")

    router.add_rule("test", counter)
    counter.read()
    assert len(router.def_output.events['test']) == 3
