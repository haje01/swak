"""Test helpers."""
import pytest

from swak.plugin import DummyOutput
from swak.datarouter import DataRouter
from swak.core import DummyAgent


@pytest.fixture()
def def_output():
    """Create default output fixture."""
    return DummyOutput()


@pytest.fixture()
def router():
    """Create data router fixture."""
    doutput = DummyOutput()
    r = DataRouter(doutput)
    doutput.router = r
    return r


@pytest.fixture()
def agent():
    """Create dummy agent for test."""
    return DummyAgent()
