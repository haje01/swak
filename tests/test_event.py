"""Test event module."""
from swak.event import MultiEventStream


def test_event_arrayevent():
    """Test ArrayEventStream."""
    times = [0, 1]
    records = [dict(k="1"), dict(k="2")]

    es = MultiEventStream(times, records)
    list(es)
    assert len([r for r in es]) == 2
