"""Test core module."""
from __future__ import absolute_import

import pytest
import click

from swak.core import parse_test_cmds, run_test_cmds, build_pipeline


def test_core_util():
    """Test core util."""
    parsed = list(parse_test_cmds('in.counter --max 4 --field 3 | out.stdout'))
    assert len(parsed) == 2
    assert parsed[0][0] == 'in.counter'
    assert parsed[0][1] == '--max'
    assert parsed[0][2] == '4'
    assert parsed[0][3] == '--field'
    assert parsed[0][4] == '3'
    assert parsed[1][0] == 'out.stdout'

    run_test_cmds(parsed)

    with pytest.raises(click.exceptions.UsageError):
        build_pipeline(parse_test_cmds('in.counter --foo 3'))

    pline = build_pipeline(parse_test_cmds('out.stdout'))
    with pytest.raises(ValueError):
        pline.validate()


