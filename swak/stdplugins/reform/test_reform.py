"""Test reform plugin."""

import socket

from .mod_reform import Reform, _tag_suffix, _normalize


def test_event_router_util():
    """Test event router utility."""
    assert ['test'] == _tag_suffix(['test'])


def test_reform_basic(router):
    """Test basic features of reform plugin."""
    writes = [('k1', 'v1'), ('k2', 'v2')]
    reform = Reform(writes, [])

    # add field
    router.add_rule("test", reform)
    router.emit("test", 0, {})
    router.flush()
    assert len(router.def_output.bulks) == 1
    assert 'k1' in router.def_output.bulks[0]
    assert 'k2' in router.def_output.bulks[0]


def test_reform_basic2(router):
    """Test delete field."""
    dels = ['k1']
    reform = Reform([], dels)
    router.add_rule("test", reform)
    records = {'k1': 'v1', 'k2': 'v2'}
    router.emit("test", 0, records)
    router.flush()
    assert len(router.def_output.bulks) == 1
    assert 'k1' not in router.def_output.bulks[0]


def test_reform_normalize():
    """Test normalizing value syntax."""
    assert '{{lit}}' == _normalize('{lit}')
    assert '{var}' == _normalize('${var}')
    assert '{var} is variable, {{lit}} is literal' ==\
        _normalize('${var} is variable, {lit} is literal')
    assert '{{{{lit}}}}' == _normalize('{{lit}}')


def test_reform_expand(router):
    """Test expand syntax."""
    # test add fields by record field & predefined variable.
    writes = [
        ("f1", "${record[f1]}_mod"),
        ("f2", "${record[f1]}_2"),
        ("host", "${hostname}"),
        ("addr", "${hostaddr}"),
        ("firsttag", "${tag_parts[0]}"),
        ("lasttag", "${tag_parts[-1]}"),
        ("first2addr", "${hostaddr_parts[0]}.${hostaddr_parts[1]}"),
        ("last2addr", "${hostaddr_parts[-2]}.${hostaddr_parts[-1]}")
    ]
    reform = Reform(writes, [])
    router.add_rule("a.b.c", reform)
    router.emit("a.b.c", 0, dict(f1="1"))
    router.flush()
    assert "host" in router.def_output.bulks[0]
    hostname = socket.gethostname()
    hostaddr = socket.gethostbyname(hostname)
    addr_parts = hostaddr.split('.')
    first2addr = "{}.{}".format(addr_parts[0], addr_parts[1])
    last2addr = "{}.{}".format(addr_parts[-2], addr_parts[-1])
    dtime, tag, record = router.def_output.bulks[0].split('\t')
    record = eval(record)

    assert record['f1'] == '1_mod'
    assert record['f2'] == '1_mod_2'
    assert record['host'] == hostname
    assert record['addr'] == hostaddr
    assert record['firsttag'] == 'a'
    assert record['lasttag'] == 'c'
    assert record['first2addr'] == first2addr
    assert record['last2addr'] == last2addr

    # check placeholders
    pholder = reform.placeholders
    assert pholder['tag'] == 'a.b.c'
    assert pholder['tag_parts'] == ['a', 'b', 'c']
    assert pholder['tag_prefix'] == ['a', 'a.b', 'a.b.c']
    assert pholder['tag_suffix'] == ['c', 'b.c', 'a.b.c']
