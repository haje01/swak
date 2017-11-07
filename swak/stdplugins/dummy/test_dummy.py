"""Test Dummy plugin."""

from .i_dummy import Dummy


def test_dummy_basic(agent):
    """Test basic features of Dummy plugin."""
    record = dict(name="john", score=123)
    dummy = Dummy(record, 3)
    agent.register_plugin("test", dummy)
    agent.simple_process(dummy)
    agent.flush(True)
    bulks = agent.def_output.bulks
    assert len(bulks) == 3
    assert 'john' in bulks[0]
