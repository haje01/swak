"""This module implements service agent test."""
from __future__ import absolute_import

import yaml

from swak.agent import ServiceAgent
from swak.plugin import ProxyOutput, ProxyInput, Modifier, Input, Output


def init_agent_from_cfg(cfgs, dryrun=False):
    """New an agent and init from config."""
    cfg = yaml.load(cfgs)
    # dry run test
    agent = ServiceAgent()
    if not agent.init_from_config(cfg, dryrun):
        return
    return agent


def test_agent_init(capfd):
    """Test service agent init."""
    cfgs = '''
sources:
    "test1":
        - m.reform -w tag test1

matches:
    "test*":
        - o.stdout
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
    assert plugins[0].recv_queues == proxy_queues


def test_agent_run():
    """Test service agent run."""
    cfgs = '''
sources:
    - i.counter | m.reform -w tag t1 | tag test1
    - i.counter | m.reform -w tag t2 | tag test2

matches:
    test*: o.stdout
    '''
    agent = init_agent_from_cfg(cfgs, False)
    agent.start()
    # check thread running
    for itrd in agent.input_threads:
        assert itrd.is_alive()
    for otrd in agent.output_threads:
        assert otrd.is_alive()
