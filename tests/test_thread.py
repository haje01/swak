"""This module implements thread test."""
from __future__ import absolute_import

from swak.stdplugins.counter.in_counter import Counter
from swak.stdplugins.stdout.out_stdout import Stdout


def test_thread_basic(router):
    """Test individual thread model."""
    cnt1 = Counter(3, 1, 0)
    cnt1.set_router(router)
    cnt1.set_tag("cnt1")

    cnt2 = Counter(3, 1, 0)
    cnt2.set_router(router)
    cnt2.set_tag("cnt2")

    stdout = Stdout()
    stdout.set_router(router)

    router.add_rule("cnt1", cnt1)
    router.add_rule("cnt2", cnt2)
    router.add_rule("cnt*", stdout)
    router.build_threads()
