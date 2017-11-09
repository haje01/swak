"""Test counter plugin."""

from .i_counter import Counter


def test_counter_basic(agent):
    """Test basic features of counter plugin."""
    counter = Counter(number=3, field=1)
    agent.register_plugin("test", counter)
    agent.simple_process(counter)
    assert len(agent.def_output.bulks) == 3
