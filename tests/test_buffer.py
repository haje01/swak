"""This module implements buffer test."""
from __future__ import absolute_import

import pytest

from swak.event import OneEventStream
from swak.chunk import Chunk
from swak.stdplugins.sized.buf_sized import Sized


def test_buffer_chunk():
    """Test buffer chunk."""
    Chunk()


def test_buffer_basic():
    """Test basic features of buffer."""
    with pytest.raises(ValueError):
        Sized(False, chunk_max_size='10k', chunk_max_record=None,
              buffer_max_chunk=None, buffer_max_size=None, flush_interval=None)

    with pytest.raises(ValueError):
        Sized(False, chunk_max_size=None, chunk_max_record=None,
              buffer_max_chunk=None, buffer_max_size='10k',
              flush_interval=None)

    buf = Sized(False, chunk_max_record=3, chunk_max_size=None,
                buffer_max_chunk=None, buffer_max_size=None,
                flush_interval=None)
    assert len(buf.chunks) == 0
    es = OneEventStream(0.1, dict(name='john', score=100))
    buf.append(es)
    assert len(buf.chunks) == 1
