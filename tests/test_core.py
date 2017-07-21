from __future__ import absolute_import

import pytest

from swak.core import parse_test_cmds, run_test_cmds
# from swak.plugin import check_plugins_initpy, enumerate_plugins


#def plugin_filter(_dir):
    #return _dir in ['counter', 'stdout']


#@pytest.fixture(scope="session", autouse=True)
#def initpy():
    #import pdb; pdb.set_trace()  # XXX BREAKPOINT
    #check_plugins_initpy(enumerate_plugins(None, plugin_filter))


def test_core_util():
    parsed = list(parse_test_cmds('in.counter --max 4 --field 3 | out.stdout'))
    assert len(parsed) == 2
    assert parsed[0][0] == 'in.counter'
    assert parsed[0][1] == '--max'
    assert parsed[0][2] == '4'
    assert parsed[0][3] == '--field'
    assert parsed[0][4] == '3'
    assert parsed[1][0] == 'out.stdout'

    run_test_cmds(parsed)

