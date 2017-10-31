"""Test counter plugin."""

from .i_counter import Counter


def test_counter_basic(agent):
    """Test basic features of counter plugin."""
    counter = Counter(3, 1, 0)
    agent.register_plugin("test", counter)
    agent.simple_process(counter, 0)
    assert len(agent.def_output.bulks) == 3
