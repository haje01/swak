"""This module implements thread test."""
from __future__ import absolute_import

from swak.stdplugins.counter.i_counter import Counter
from swak.stdplugins.stdout.o_stdout import Stdout


def test_thread_basic(sagent):
    """Test service agent building threads."""
    cnt1 = Counter(3, 1, 0)
    sagent.register_plugin("cnt1", cnt1)

    cnt2 = Counter(3, 1, 0)
    sagent.register_plugin("cnt2", cnt2)

    stdout = Stdout()
    sagent.register_plugin("cnt*", stdout)

    sagent.build_threads()
