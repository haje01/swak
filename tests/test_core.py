"""This module implements core module test."""

from __future__ import absolute_import

import pytest
import click

from swak.core import TRunAgent
from swak.plugin import Output


def test_core_test_run():
    """Test core test run."""
    # First plugin must be an input plugin.
    with pytest.raises(ValueError):
        list(TRunAgent._parse_and_validate_cmds("m.reform"))

    cmds = list(TRunAgent._parse_and_validate_cmds('i.counter --count 4 '
                                                   '--field 3'))
    assert len(cmds) == 1
    assert cmds[0][0] == 'i.counter'
    assert cmds[0][1] == '--count'
    assert cmds[0][2] == '4'
    assert cmds[0][3] == '--field'

    agent = TRunAgent()
    router = agent._init_from_commands(cmds, True)
    assert router is not None
    # process events from input
    agent.simple_process(agent.plugins[0])
    bulks = agent.def_output.bulks
    assert len(bulks) == 4
    _, _, record = bulks[0].split('\t')
    record = eval(record)
    assert record == dict(f1=1, f2=1, f3=1)

    with pytest.raises(click.exceptions.UsageError):
        cmds = 'i.counter --foo 3'
        cmds = TRunAgent._parse_and_validate_cmds(cmds)
        agent._init_from_commands(cmds, True)

    agent = TRunAgent()
    agent.run_commands('i.counter | m.reform -w host ${hostname} -w tag ${tag}'
                       ' -d tag')
    _, _, record = agent.def_output.bulks[0].split('\t')
    record = eval(record)
    assert len(record) == 2
    assert 'host' in record      # inserted
    assert 'tag' not in record   # deleted (overrided)


def test_core_agent_basic(agent):
    """Test event router iter plugin."""
    # iterate plugin test. if no output plugin exists, last plugin is
    #  default output.
    plugins = [plugin for plugin in agent.iter_plugins()]
    assert isinstance(plugins[-1], Output)
