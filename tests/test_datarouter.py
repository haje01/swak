"""This module implements    test."""
import time

import pytest

from swak.stdplugins.filter.m_filter import Filter
from swak.stdplugins.reform.m_reform import Reform
from swak.plugin import DummyOutput


@pytest.fixture()
def output():
    """Create stdoutput and returns it."""
    return DummyOutput()


@pytest.fixture()
def filter():
    """Create filter plugin and returns it."""
    return Filter([("k", "V")])


def test_datarouter_pipeline(agent):
    """Test data router cache."""
    router = agent.router
    assert len(router.match_cache) == 0
    router.emit("a.b.c", 0, {"k": "v"})
    assert len(router.match_cache) == 1


def test_datarouter_basic(agent, output):
    """Test data router."""
    # router with only default output.
    agent.register_plugin("test", output)
    router = agent.router
    router.emit("test", time.time(), {"k": "v"})
    agent.flush()
    assert len(output.bulks) == 1


def test_datarouter_basic2(agent, output):
    """Test data router with an output."""
    agent.register_plugin("test", output)
    router = agent.router
    router.emit("test", time.time(), {"k": "v"})
    agent.flush()
    assert len(output.bulks) == 1


def test_datarouter_basic3(agent, output, filter):
    """Test data router with modifier & output."""
    router = agent.router
    assert len(output.bulks) == 0
    agent.register_plugin("test", filter)
    agent.register_plugin("test", output)
    router.emit("test", time.time(), {"k": "v"})
    agent.flush()
    # the record filtered out.
    assert len(output.bulks) == 0

    # unmatched data goes to default output
    router.emit("foo", time.time(), {"k": "v"})
    agent.flush()
    assert 'foo' in router.def_output.buffer.chunks[0].bulk[0]
    assert len(output.bulks) == 0


def flush_and_get_record(agent):
    """Flush given router and get record."""
    agent.flush()
    return eval(agent.router.def_output.bulks[0].split('\t')[2])


def test_datarouter_complex(agent):
    r"""Test V shaped data router.

    a     b
     \   /
       c
    """
    router = agent.router
    reform_a = Reform([('a', "1")])
    reform_b = Reform([('b', "2")])
    reform_c = Reform([('c', "3")])

    agent.register_plugin("a", reform_a)
    agent.register_plugin("b", reform_b)
    agent.register_plugin("*", reform_c)

    # Pipeline: a -> c
    router.def_output.reset()
    router.emit("a", 0, {})

    record = flush_and_get_record(agent)
    assert dict(a="1", c="3") == record

    # Pipeline: b -> c
    router.def_output.reset()
    router.emit("b", 0, {})
    record = flush_and_get_record(agent)
    assert dict(b="2", c="3") == record

    # Pipeline: c
    router.def_output.reset()
    router.emit("c", 0, {})
    record = flush_and_get_record(agent)
    assert dict(c="3") == record

    # Check generated pipeline structure
    assert {'a', 'b', 'c'} == set(router.match_cache.keys())
    assert len(router.match_cache['a'].modifiers) == 2
    assert len(router.match_cache['b'].modifiers) == 2
    assert len(router.match_cache['c'].modifiers) == 1
