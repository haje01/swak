"""Test buffer plugin of Memory."""

from swak import stdplugins as stp

from .buf_memory import Memory


def test_memory_basic(router):
    """Test basic features of Memory."""
    counter = stp.counter.in_counter.Counter(3, 1, 0)
    counter.set_router(router)
    counter.set_tag('test')

    buffer = Memory()
    router.def_output.set_buffer(buffer)

    router.add_rule('test', counter)
    counter.read()
