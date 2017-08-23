"""Test event router."""
import time

import pytest

from swak.event_router import EventRouter
from common import DummyOutput


@pytest.fixture()
def def_output():
    """Create default output and returns it."""
    return DummyOutput()


@pytest.fixture()
def filter():
    """Create default filter and returns it."""
    pass


@pytest.fixture()
def output():
    """Create default output and returns it."""
    pass


def test_event_router(def_output, filter, output):
    """Test event router."""
    event_router = EventRouter(def_output)
    event_router.emit("test", time.time(), {"k": "v"})
    assert len(def_output.events) == 1

    # event_router.add_rule("test", filter)
    # event_router.add_rule("test", output)

    # event_router.emit("test", time.time(), {"k": "v"})
