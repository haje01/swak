"""Test core module."""
from __future__ import absolute_import

import pytest
import click

from swak.core import parse_and_validate_test_cmds,\
    run_test_cmds, build_test_event_router
from swak.const import TEST_STREAM_TAG


def test_core_test_cmd():
    """Test core util."""
    # First plugin must be an input plugin.
    with pytest.raises(ValueError):
        list(parse_and_validate_test_cmds("mod.reform"))

    cmds = list(parse_and_validate_test_cmds('in.counter --max 4 --field 3'))
    assert len(cmds) == 1
    assert cmds[0][0] == 'in.counter'
    assert cmds[0][1] == '--max'
    assert cmds[0][2] == '4'
    assert cmds[0][3] == '--field'

    router = run_test_cmds(cmds, True)
    records = router.default_output.events[TEST_STREAM_TAG]
    assert len(records) == 4
    record = records[0][1]
    assert record == dict(f1=1, f2=1, f3=1)

    with pytest.raises(click.exceptions.UsageError):
        build_test_event_router(parse_and_validate_test_cmds('in.counter --foo'
                                                             ' 3'))

    cmds = parse_and_validate_test_cmds('in.counter | mod.reform -a aaa 111')
    router = run_test_cmds(cmds)
    record = router.default_output.events[TEST_STREAM_TAG][0][1]
    assert len(record) == 2
