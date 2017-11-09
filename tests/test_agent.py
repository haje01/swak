"""This module implements service agent test."""
from __future__ import absolute_import

import yaml
import time

from swak.agent import ServiceAgent
from swak.plugin import ProxyOutput, ProxyInput, Modifier, Input, Output


def init_agent_from_cfg(cfgs, dryrun=False):
    """New an agent and init from config."""
    cfg = yaml.load(cfgs)
    # dry run test
    agent = ServiceAgent()
    if not agent.init_from_cfg(cfg, dryrun):
        return
    return agent


def test_agent_init(capfd):
    """Test service agent init."""
    cfgs = '''
sources:
    "test1":
        - m.reform -w tag test1

matches:
    "test*": o.stdout
    '''
    agent = init_agent_from_cfg(cfgs, False)
    out, err = capfd.readouterr()
    assert "'sources' field must be a list" in err

    cfgs = '''
sources:
    - i.counter | m.reform -w tag test1

matches:
    test:
        - o.stdout
    '''
    agent = init_agent_from_cfg(cfgs, False)
    out, err = capfd.readouterr()
    assert "must ends with a tag command or output plugin" in err

    # single thread for input & output
    cfgs = '''
sources:
    - i.counter | m.reform -w tag t1 | o.stdout
    '''
    # dry run test
    agent = init_agent_from_cfg(cfgs, True)
    out, err = capfd.readouterr()
    assert len(err) == 0

    # seperate threads for input & output
    cfgs = '''
sources:
    - i.counter | m.reform -w tag t1 | tag test1
    - i.counter | m.reform -w tag t2 | tag test2

matches:
    test*: o.stdout
    '''
    # dry run test
    agent = init_agent_from_cfg(cfgs, True)
    out, err = capfd.readouterr()
    assert len(err) == 0
    assert len(agent.input_threads) == 0
    assert len(agent.output_threads) == 0

    # real run test
    agent = init_agent_from_cfg(cfgs, False)
    assert len(agent.input_threads) == 2
    assert len(agent.output_threads) == 1

    # check input thread
    proxy_queues = []
    for itrd in agent.input_threads:
        assert itrd.pluginpod.router is not None
        plugins = itrd.pluginpod.plugins
        assert len(plugins) == 3
        assert isinstance(plugins[0], Input)
        assert isinstance(plugins[1], Modifier)
        assert isinstance(plugins[2], ProxyOutput)
        proxy_output = plugins[2]
        queue = proxy_output.send_queue
        assert queue is not None
        proxy_queues.append(queue)

    # check output thread
    otrd = agent.output_threads[0]
    assert otrd.pluginpod.router is not None
    plugins = otrd.pluginpod.plugins
    assert len(plugins) == 2
    assert isinstance(plugins[0], ProxyInput)
    assert isinstance(plugins[1], Output)
    assert set(plugins[0].recv_queues.values()) == set(proxy_queues)


def test_agent_run_sep(capsys):
    """Test service agent run."""
    # Seperated thread model.
    cfgs = '''
logger:
    root:
        level: CRITICAL

sources:
    - i.counter -d 1 | o.stdout
    '''
    agent = init_agent_from_cfg(cfgs, False)
    agent.start()
    assert len(agent.input_threads) == 1
    for itrd in agent.input_threads:
        assert itrd.is_alive()
    assert len(agent.output_threads) == 0
    time.sleep(0.2)
    out, err = capsys.readouterr()
    assert len(err) == 0
    assert "'f1': 1" in out

    time.sleep(1)
    out, err = capsys.readouterr()
    assert len(err) == 0
    assert "'f1': 2" in out

    time.sleep(1)
    out, err = capsys.readouterr()
    assert len(err) == 0
    assert "'f1': 3" in out

    agent.stop()
    agent.shutdown()

    # Aggregated thread model.
    cfgs = '''
logger:
    root:
        level: CRITICAL

sources:
    - i.counter -d 1 | m.reform -w tag t1 | tag test1
    - i.counter -d 1 | m.reform -w tag t2 | tag test2

matches:
    test*: o.stdout b.memory -f 1
    '''
    agent = init_agent_from_cfg(cfgs, False)
    agent.start()
    # check thread running
    for itrd in agent.input_threads:
        assert itrd.is_alive()
    for otrd in agent.output_threads:
        assert otrd.is_alive()

    out, err = capsys.readouterr()
    assert len(err) == 0
    assert "'f1'" not in out  # because of the output buffer

    time.sleep(1)
    out, err = capsys.readouterr()
    assert len(err) == 0
    assert "'f1': 1" in out
    assert "'tag': 't1'" in out
    assert "'tag': 't2'" in out
    assert "'f1': 2" not in out

    time.sleep(1)
    out, err = capsys.readouterr()
    assert len(err) == 0
    assert "'f1': 2" in out
    assert "'tag': 't1'" in out
    assert "'tag': 't2'" in out
    assert "'f1': 3" not in out

    agent.stop()
    agent.shutdown()

    # finally flushed.
    out, err = capsys.readouterr()
    assert len(err) == 0
    assert "'f1': 3" in out
