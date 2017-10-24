"""This module implements service agent test."""
from __future__ import absolute_import

import yaml

from swak.agent import ServiceAgent


def init_agent_from_cfg(cfgs, dryrun=False):
    """New an agent and init from config."""
    cfg = yaml.load(cfgs)
    # dry run test
    agent = ServiceAgent()
    if not agent.init_from_config(cfg, dryrun):
        return
    return agent


def test_agent_threads(capfd):
    """Test agent init threads."""
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
    assert "must ends with a tag" in err

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

    for itrd in agent.input_threads:
        assert itrd.pluginpod.router is not None
