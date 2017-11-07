"""This module implements data test."""
from swak.data import MultiDataStream


def test_data_basic():
    """Test data stream."""
    times = [0, 1]
    records = [dict(k="1"), dict(k="2")]

    ds = MultiDataStream(times, records)
    list(ds)
    assert len([r for r in ds]) == 2
    assert len(ds) == 2
