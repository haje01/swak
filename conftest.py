"""Test helpers."""
import pytest

from swak.plugin import DummyOutput
from swak.event_router import EventRouter
from swak.core import DummyAgent, ServiceAgent


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


@pytest.fixture()
def agent():
    """Create dummy agent for test."""
    return DummyAgent()


@pytest.fixture()
def sagent():
    """Create service agent for test."""
    doutput = DummyOutput()
    return ServiceAgent(doutput)
