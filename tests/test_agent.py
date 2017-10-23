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


def test_agent_threads():
    """Test agent init threads."""
    cfgs = '''
sources:
    "test1":
        - i.counter | m.reform -w tag test1
    "test2":
        - i.counter | m.reform -w tag test2

matches:
    "test*":
        - o.stdout
    '''
    # dry run test
    agent = init_agent_from_cfg(cfgs, True)
    assert len(agent.input_threads) == 0
    assert len(agent.output_threads) == 0

    # real run test
    agent = init_agent_from_cfg(cfgs, False)
    assert len(agent.input_threads) == 2
    assert len(agent.output_threads) == 1
