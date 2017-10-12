"""This module implements buffer test."""
from __future__ import absolute_import

import time

import pytest

from swak.buffer import MemoryBuffer


def test_buffer_chunk():
    """Test buffer chunk."""


def test_buffer_basic():
    """Test basic features of buffer."""
    # arguments validation
    with pytest.raises(ValueError):
        MemoryBuffer(None, False, chunk_max_record=0)
    with pytest.raises(ValueError):
        MemoryBuffer(None, False, buffer_max_chunk=0)
    with pytest.raises(ValueError):
        MemoryBuffer(None, False, chunk_max_size='0')
    with pytest.raises(ValueError):
        MemoryBuffer(None, False, flush_interval='0')

    # chunking by chunk_max_record.
    buf = MemoryBuffer(None, False, chunk_max_record=1, buffer_max_chunk=2)
    assert len(buf.chunks) == 1  # initial chunk
    # append first
    buf.append("formatted event1")
    assert len(buf.chunks) == 1
    prev_chunk = buf.active_chunk
    assert prev_chunk.bytesize == 16
    assert buf.cnt_chunking == 0
    assert buf.cnt_flushing == 0
    # append second, chunk flushed and new chunk created.
    # 1. chunking by chunk_max_record
    # 2. flushing by buffer_max_chunk
    # 3. concat data
    buf.append("formatted event2")
    assert buf.active_chunk != prev_chunk
    assert len(buf.chunks) == 1
    assert buf.cnt_chunking == 1
    assert buf.cnt_flushing == 1

    # chunking by chunk_max_size.
    buf = MemoryBuffer(None, False, chunk_max_size='16', buffer_max_chunk=2)
    assert len(buf.chunks) == 1  # initial chunk
    # append first
    buf.append("formatted event1")
    assert len(buf.chunks) == 1
    prev_chunk = buf.active_chunk
    assert buf.cnt_chunking == 0
    assert buf.cnt_flushing == 0
    # append second, chunk flushed and new chunk created.
    buf.append("formatted event2")
    assert buf.active_chunk != prev_chunk
    assert buf.active_chunk.bytesize == 16
    assert len(buf.chunks) == 1
    assert buf.cnt_chunking == 1
    assert buf.cnt_flushing == 1

    # flushing by flush_interval.
    buf = MemoryBuffer(None, False, flush_interval='1s')
    assert len(buf.chunks) == 1  # initial chunk
    # append first
    buf.append("formatted event1")
    assert len(buf.chunks) == 1  # no chunking yet.
    prev_chunk = buf.active_chunk
    assert buf.cnt_chunking == 0
    assert buf.cnt_flushing == 0
    time.sleep(1)
    # append process:
    # 1. flushing by interval
    # 2. new chunk created since there are no left chunks after flushing.
    # 3. concat new event to new chunk
    buf.append("formatted event2")
    assert len(buf.chunks) == 1
    assert buf.active_chunk != prev_chunk
    # new chunk has beed created since there are no chunks after flushing.
    assert buf.active_chunk.bytesize == 16
    assert buf.cnt_flushing == 1
    assert buf.cnt_chunking == 1

    # flushing by buffer_max_chunk
    buf = MemoryBuffer(None, False, chunk_max_record=1, buffer_max_chunk=2)
    buf.append("event1")
    # no chunking yet
    assert buf.cnt_chunking == 0
    # append process
    # 1. chunking occur by chunk_max_record
    # 2. flushing occur by buffer_max_chunk
    # 3. concat new event to new chunk
    buf.append("event2")
    assert buf.cnt_chunking == 1
    assert buf.cnt_flushing == 1
    assert len(buf.chunks) == 1
