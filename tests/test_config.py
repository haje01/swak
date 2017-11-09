"""This module implements service agent test."""
from __future__ import absolute_import

import yaml

from swak.config import main_logger_config
from swak.agent import ServiceAgent


def init_agent_from_cfg(cfgs, dryrun=False):
    """New an agent and init from config."""
    cfg = yaml.load(cfgs)
    # dry run test
    agent = ServiceAgent()
    if not agent.init_from_cfg(cfg, dryrun):
        return
    return agent


def assert_cfg_error(cfgs, capsys, emsg):
    """Assert config error message."""
    init_agent_from_cfg(cfgs)
    _, err = capsys.readouterr()
    assert emsg in err


def test_config_logger():
    """Test logger config."""
    update_cfg = {
        'logger': {
            'root': {
                'level': 'ERROR'
            }
        }
    }
    cfg = main_logger_config(update_cfg)
    assert cfg['logger']['version'] == 1
    assert cfg['logger']['root']['level'] == 'ERROR'


def test_config_init(capsys):
    """Test agent init config."""
    # test malformed config
    assert_cfg_error('''
    ''', capsys, "No content")
    assert_cfg_error('''
sources:
    ''', capsys, "'sources' field has no declaration")

    assert_cfg_error('''
sources:
    "test": i.counter
    ''', capsys, "'sources' field must be a list")
    assert_cfg_error('''
sources:
    - o.stdout
    ''', capsys, "commands must starts with input")
    assert_cfg_error('''
sources:
    - i.counter
    ''', capsys, "commands must ends with a tag command")
    assert_cfg_error('''
sources:
    - {}
    ''', capsys, "each source must be a string")
    assert_cfg_error('''
sources:
    - i.counter | tag foo
matches:
    ''', capsys, "'matches' field has no declaration")
    assert_cfg_error('''
sources:
    - i.counter | tag foo
matches:
    - o.stdout
    ''', capsys, "'matches' field must be a dictionary")
    assert_cfg_error('''
sources:
    - i.counter | tag foo
matches:
    foo: {}
    ''', capsys, "each match must be a string")
    assert_cfg_error('''
sources:
    - i.counter | tag foo
matches:
    boo:
        - o.stdout
    ''', capsys, "each match must be a string.")
    assert_cfg_error('''
sources:
    - i.counter | tag foo
matches:
    boo: o.stdout
    ''', capsys, "tag 'foo' does not have corresponding match tag.")
