"""Test helpers."""
import pytest

from swak.plugin import DummyOutput
from swak.event_router import EventRouter


@pytest.fixture()
def def_output():
    """Create default output fixture."""
    return DummyOutput()


@pytest.fixture()
def router():
    """Create event router fixture."""
    doutput = DummyOutput()
    r = EventRouter(doutput)
    doutput.router = r
    return r
