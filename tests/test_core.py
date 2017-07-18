from __future__ import absolute_import

import pytest

from swak.core import parse_test_cmds, run_test_cmds


@pytest.fixture(scope="session", autouse=True)
def plugins_initpy():
    from swak.plugin import enumerate_plugins, check_plugins_initpy
    check_plugins_initpy(enumerate_plugins())


def test_core_util():
    parsed = list(parse_test_cmds('in.counter --fields 3 | out.stdout'))
    assert len(parsed) == 2
    assert parsed[0][0] == 'in.counter'
    assert parsed[0][1] == '--fields'
    assert parsed[0][2] == '3'
    assert parsed[1][0] == 'out.stdout'

    run_test_cmds(parsed)

