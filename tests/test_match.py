"""Test match."""

from swak.match import GlobMatchPattern
from swak.event_router import Rule


def assert_glob_match(ptrn, samp):
    """Assert glob match."""
    assert GlobMatchPattern(ptrn).match(samp)


def assert_glob_not_match(ptrn, samp):
    """Assert glob not match."""
    assert not GlobMatchPattern(ptrn).match(samp)


def assert_or_match(pats, str):
    """Assert or pattern match."""
    assert Rule(pats, None).match(str)


def assert_or_not_match(pats, str):
    """Assert or pattern not match."""
    assert not Rule(pats, None).match(str)


def test_simple():
    """Test simple cases."""
    assert_glob_match('a', 'a')
    assert_glob_match('a.b', 'a.b')
    assert_glob_not_match('a', 'b')


def test_wildcard():
    """Test wildcard."""
    assert_glob_match('a*', 'a')
    assert_glob_match('a*', 'ab')
    assert_glob_match('a*', 'abc')

    assert_glob_match('*a', 'a')
    assert_glob_match('*a', 'ba')
    assert_glob_match('*a', 'cba')

    assert_glob_match('*a*', 'a')
    assert_glob_match('*a*', 'ba')
    assert_glob_match('*a*', 'ac')
    assert_glob_match('*a*', 'bac')

    assert_glob_not_match('a*', 'a.b')
    assert_glob_not_match('a*', 'ab.c')
    assert_glob_not_match('a*', 'ba')
    assert_glob_not_match('*a', 'ab')

    assert_glob_match('a.*', 'a.b')
    assert_glob_match('a.*', 'a.c')
    assert_glob_not_match('a.*', 'ab')

    assert_glob_match('a.*.c', 'a.b.c')
    assert_glob_match('a.*.c', 'a.c.c')

    assert_glob_not_match('a.*.c', 'a.c')


def test_recursive_wildcard():
    """Test recursive wildcard."""
    assert_glob_match('a.**', 'a')
    assert_glob_not_match('a.**', 'ab')
    assert_glob_not_match('a.**', 'abc')
    assert_glob_match('a.**', 'a.b')
    assert_glob_not_match('a.**', 'ab.c')
    assert_glob_not_match('a.**', 'ab.d.e')

    assert_glob_match('a**', 'a')
    assert_glob_match('a**', 'ab')
    assert_glob_match('a**', 'abc')
    assert_glob_match('a**', 'a.b')
    assert_glob_match('a**', 'ab.c')
    assert_glob_match('a**', 'ab.d.e')

    assert_glob_match('**.a', 'a')
    assert_glob_not_match('**.a', 'ba')
    assert_glob_not_match('**.a', 'c.ba')
    assert_glob_match('**.a', 'b.a')
    assert_glob_match('**.a', 'cb.a')
    assert_glob_match('**.a', 'd.e.a')

    assert_glob_match('**a', 'a')
    assert_glob_match('**a', 'ba')
    assert_glob_match('**a', 'c.ba')
    assert_glob_match('**a', 'b.a')
    assert_glob_match('**a', 'cb.a')
    assert_glob_match('**a', 'd.e.a')


def test_or():
    """Test or pattern match."""
    assert_glob_match('a.{b,c}', 'a.b')
    assert_glob_match('a.{b,c}', 'a.c')
    assert_glob_not_match('a.{b,c}', 'a.d')

    assert_glob_match('a.{b,c}.**', 'a.b')
    assert_glob_match('a.{b,c}.**', 'a.c')
    assert_glob_not_match('a.{b,c}.**', 'a.d')
    assert_glob_not_match('a.{b,c}.**', 'a.cd')

    assert_glob_match('a.{b.**,c}', 'a.b')
    assert_glob_match('a.{b.**,c}', 'a.b.c')
    assert_glob_match('a.{b.**,c}', 'a.c')
    assert_glob_not_match('a.{b.**,c}', 'a.c.d')


def test_multi_pattern_or():
    """Test multi pattern."""
    assert_or_match('a.b a.c', 'a.b')
    assert_or_match('a.b a.c', 'a.c')
    assert_or_not_match('a.b a.c', 'a.d')

    assert_or_match('a.b.** a.c.**', 'a.b')
    assert_or_match('a.b.** a.c.**', 'a.c')
    assert_or_not_match('a.b.** a.c.**', 'a.d')
    assert_or_not_match('a.b.** a.c.**', 'a.cd')

    assert_or_match('a.b.** a.c', 'a.b')
    assert_or_match('a.b.** a.c', 'a.b.c')
    assert_or_match('a.b.** a.c', 'a.c')
    assert_or_not_match('a.b.** a.c', 'a.c.d')
