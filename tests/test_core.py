"""This module implements core module test."""

from __future__ import absolute_import

import time

import pytest
import click

from swak.core import TRunAgent
from swak.plugin import Output
from swak.util import parse_and_validate_cmds
from swak.const import TESTRUN_TAG


def init_agent_with_cmds(cmds):
    """Init agnet with test run commands."""
    cmds = parse_and_validate_cmds(cmds, True, False)
    agent = TRunAgent()
    input_pl = agent.init_from_commands(TESTRUN_TAG, cmds)
    return agent, input_pl


def test_core_testrun(capfd):
    """Test test run relations."""
    # test parse and validate commands
    cmds = parse_and_validate_cmds('i.counter --count 4 --field 3', True,
                                   False)
    assert len(cmds) == 1
    assert cmds[0][0] == 'i.counter'
    assert cmds[0][1] == '--count'
    assert cmds[0][2] == '4'
    assert cmds[0][3] == '--field'

    agent = TRunAgent()
    input_pl = agent.init_from_commands(TESTRUN_TAG, cmds)
    assert input_pl is not None
    # process events from input
    agent.simple_process(agent.pluginpod.plugins[0], 0.0)
    bulks = agent.def_output.bulks
    assert len(bulks) == 4
    _, _, record = bulks[0].split('\t')
    record = eval(record)
    assert record == dict(f1=1, f2=1, f3=1)

    with pytest.raises(click.exceptions.UsageError):
        cmds = 'i.counter --foo 3'
        cmds = parse_and_validate_cmds(cmds, True, False)
        agent.init_from_commands(TESTRUN_TAG, cmds)

    # test run with reform
    agent = TRunAgent()
    agent.run_commands('i.counter | m.reform -w host ${hostname} -w tag ${tag}'
                       ' -d tag', 0.0)
    _, _, record = agent.def_output.bulks[0].split('\t')
    record = eval(record)
    assert len(record) == 2
    assert 'host' in record      # inserted
    assert 'tag' not in record   # deleted (overrided)
    capfd.readouterr()  # flush stdout/err

    # test run with buffer
    agent = TRunAgent()
    agent.run_commands('i.counter | o.stdout b.memory -f 1', 0.0)
    out, _ = capfd.readouterr()
    # check number of lines
    assert len(out.strip().split('\n')) == 3


def test_core_agent_process(capfd):
    """Test agent processing."""
    cmds = 'i.counter | o.stdout b.memory -c 1 -r 1'
    agent, input_pl = init_agent_with_cmds(cmds)
    # first process
    agent.simple_process_one(input_pl)
    out, _ = capfd.readouterr()
    # no output for buffer_max_chunk == 1
    assert out == ''
    # second process
    agent.simple_process_one(input_pl)
    # first output
    out, _ = capfd.readouterr()
    assert len(out.strip().split('\n')) == 1
    assert "'f1': 1" in out
    agent.simple_process_one(input_pl)
    # second output
    out, _ = capfd.readouterr()
    assert "'f1': 2" in out

    cmds = 'i.counter | o.stdout b.memory -f 1'
    agent, input_pl = init_agent_with_cmds(cmds)
    # first process
    agent.simple_process_one(input_pl)
    out, _ = capfd.readouterr()
    # no output for flush interval
    assert out == ''
    time.sleep(1)
    agent.simple_process_one(input_pl)
    out, _ = capfd.readouterr()
    # first, second output after sleep
    assert "'f1': 1" in out
    assert "'f1': 2" in out
    assert len(out.strip().split('\n')) == 2
    agent.simple_process_one(input_pl)
    out, _ = capfd.readouterr()
    # no output immediately
    assert out == ''
    time.sleep(1)
    # third output after sleep
    agent.simple_process_one(input_pl)
    out, _ = capfd.readouterr()
    assert "'f1': 3" in out


def test_core_agent_basic(agent):
    """Test event router iter plugin."""
    # iterate plugin test. if no output plugin exists, last plugin is
    #  default output.
    plugins = [plugin for plugin in agent.pluginpod.iter_plugins()]
    assert isinstance(plugins[-1], Output)
