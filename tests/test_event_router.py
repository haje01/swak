"""Test event router."""
import time

import pytest

from swak.event_router import EventRouter
from swak.plugin import DummyOutput


@pytest.fixture()
def def_output():
    """Create default output and returns it."""
    return DummyOutput()


@pytest.fixture()
def reform():
    """Create default reform and returns it."""
    pass


@pytest.fixture()
def output():
    """Create default output and returns it."""
    return DummyOutput()


def test_event_router(def_output, reform, output):
    """Test event router."""
    # router with only default output.
    event_router = EventRouter(def_output)
    event_router.emit("test", time.time(), {"k": "v"})
    assert len(def_output.events['test']) == 1

    # router with an output
    event_router = EventRouter(def_output)
    event_router.add_rule("test", output)
    event_router.emit("test", time.time(), {"k": "v"})
    assert len(output.events['test']) == 1

    # router with reform & output.
    event_router = EventRouter(def_output)
    event_router.add_rule("test", reform)
    event_router.add_rule("test", output)

    # event_router.emit("test", time.time(), {"k": "v"})
