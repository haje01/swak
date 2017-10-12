"""This module implements core module test."""

from __future__ import absolute_import

import pytest
import click

from swak.core import parse_and_validate_test_cmds,\
    run_test_cmds, build_test_event_router


def test_core_test_cmd():
    """Test core util."""
    # First plugin must be an input plugin.
    with pytest.raises(ValueError):
        list(parse_and_validate_test_cmds("m.reform"))

    cmds = list(parse_and_validate_test_cmds('i.counter --count 4 --field 3'))
    assert len(cmds) == 1
    assert cmds[0][0] == 'i.counter'
    assert cmds[0][1] == '--count'
    assert cmds[0][2] == '4'
    assert cmds[0][3] == '--field'

    router = run_test_cmds(cmds, True)
    bulks = router.def_output.bulks
    assert len(bulks) == 4
    _, _, record = bulks[0].split('\t')
    record = eval(record)
    assert record == dict(f1=1, f2=1, f3=1)

    with pytest.raises(click.exceptions.UsageError):
        build_test_event_router(parse_and_validate_test_cmds('i.counter --foo'
                                                             ' 3'))

    cmds = parse_and_validate_test_cmds('i.counter | m.reform -w host '
                                        '${hostname} -w tag ${tag} -d tag')
    router = run_test_cmds(cmds, True)
    _, _, record = router.def_output.bulks[0].split('\t')
    record = eval(record)
    assert len(record) == 2
    assert 'host' in record      # inserted
    assert 'tag' not in record   # deleted (overrided)
