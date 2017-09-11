"""Test {{class_name}} plugin."""

import pytest

from swak.plugin import DummyOutput
from swak.event_router import EventRouter


@pytest.fixture()
def def_output():
    """Create default output and returns it."""
    return DummyOutput()


def test_{{class_name|lower}}_basic(def_output):
    """Test basic features of {{class_name}} plugin."""
    pass
