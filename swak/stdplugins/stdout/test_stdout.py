"""Test stdout plugin."""

from swak.stdplugins.counter.in_counter import Counter

from .out_stdout import Stdout


def test_stdout_basic(router, capfd):
    """Test basic features of Stdout plugin."""
    counter = Counter(3, 1, 0)
    counter.set_router(router)
    counter.set_tag("test")
    stdout = Stdout()
    stdout.set_router(router)

    router.add_rule("test", counter)
    router.add_rule("test", stdout)
    counter.read()
    out, err = capfd.readouterr()
    lines = out.strip().split('\n')
    assert len(lines) == 3
    elms = lines[0].split('\t')
    assert elms[1] == 'test'
    assert 'f1' in elms[2]
