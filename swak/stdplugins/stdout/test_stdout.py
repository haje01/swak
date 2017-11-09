"""Test stdout plugin."""

from swak.core import TRunAgent
from swak.stdplugins.counter.i_counter import Counter

from .o_stdout import Stdout


def test_stdout_basic(agent, capfd):
    """Test basic features of Stdout plugin."""
    counter = Counter(3, 1, 0)
    agent.register_plugin("test", counter)
    stdout = Stdout()
    agent.register_plugin("test", stdout)
    agent.simple_process(counter)
    agent.flush(True)

    out, err = capfd.readouterr()
    lines = out.strip().split('\n')
    assert len(lines) == 3
    elms = lines[0].split('\t')
    assert elms[1] == 'test'
    assert 'f1' in elms[2]


def test_stdout_cmds(capsys):
    """Test stdout with trun cmds."""
    TRunAgent().run_commands('i.counter -n 3 | o.stdout b.memory')
    out, err = capsys.readouterr()
    assert err == ''
    assert "'f1': 3" in out
