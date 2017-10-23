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


def assert_cfg_error(cfgs, capsys, emsg):
    """Assert config error message."""
    assert not init_agent_from_cfg(cfgs)
    _, err = capsys.readouterr()
    assert emsg in err


def test_agent_config(capsys):
    """Test agent config."""
    # test malformed config
    assert_cfg_error('''
    ''', capsys, "No content")
    assert_cfg_error('''
sources:
    ''', capsys, "'sources' field has no declaration")

    assert_cfg_error('''
sources:
    - i.counter
    ''', capsys, "'sources' field must be a dictionary")
    assert_cfg_error('''
sources:
    "test": o.stdout
    ''', capsys, "A source should start with input plugin")
    assert_cfg_error('''
sources:
    "test": {}
    ''', capsys, "each source must be a string or a list")
    assert_cfg_error('''
sources:
    "test": i.counter
    ''', capsys, "No 'matches' field")
    assert_cfg_error('''
sources:
    "test": i.counter
matches:
    ''', capsys, "'matches' field has no declaration")
    assert_cfg_error('''
sources:
    "test": i.counter
matches:
    - o.stdout
    ''', capsys, "'matches' field must be a dictionary")
    assert_cfg_error('''
sources:
    "test": i.counter
matches:
    "test": {}
    ''', capsys, "each match must be a string or a list")
    assert_cfg_error('''
sources:
    "test": i.counter
matches:
    "foo": o.stdout
    ''', capsys, "tag 'test' does not have corresponding match tag.")
