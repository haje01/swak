"""This module implements buffer test."""
from __future__ import absolute_import

import time

import pytest

from swak.buffer import MemoryBuffer
from swak.exception import ConfigError


def test_buffer_chunk():
    """Test buffer chunk."""


def test_buffer_basic():
    """Test basic features of buffer."""
    # arguments validation
    with pytest.raises(ConfigError):
        MemoryBuffer(None, False, chunk_max_record=0)
    with pytest.raises(ConfigError):
        MemoryBuffer(None, False, buffer_max_chunk=0)
    with pytest.raises(ConfigError):
        MemoryBuffer(None, False, chunk_max_size='0')
    with pytest.raises(ConfigError):
        MemoryBuffer(None, False, flush_interval='0')

    # chunking by chunk_max_record.
    buf = MemoryBuffer(None, False, chunk_max_record=1, buffer_max_chunk=1)
    assert len(buf.chunks) == 1  # initial chunk
    # append first
    prev_chunk = buf.active_chunk
    buf.append("formatted data1")
    assert prev_chunk == buf.active_chunk
    assert buf.cnt_chunking == 0
    assert buf.active_chunk == prev_chunk
    assert prev_chunk.num_record == 1
    assert prev_chunk.bytesize == 15
    assert buf.cnt_chunking == 0
    buf.may_flushing()
    assert prev_chunk == buf.active_chunk
    assert buf.active_chunk.num_record == 1
    assert buf.active_chunk.bytesize == 15
    assert len(buf.chunks) == 1
    assert buf.cnt_flushing == 0
    buf.append("formatted data2")
    assert prev_chunk != buf.active_chunk
    assert buf.cnt_chunking == 1
    assert buf.cnt_flushing == 0
    assert prev_chunk.num_record == 1
    assert prev_chunk.bytesize == 15
    assert buf.active_chunk.num_record == 1
    assert buf.active_chunk.bytesize == 15
    only_chunk = buf.may_flushing()
    assert only_chunk is None
    assert buf.cnt_flushing == 1
    assert len(buf.chunks) == 1

    # chunking by chunk_max_size.
    buf = MemoryBuffer(None, False, chunk_max_size='20', buffer_max_chunk=1)
    assert len(buf.chunks) == 1  # initial chunk
    # append first
    prev_chunk = buf.active_chunk
    buf.append("formatted data1")
    assert prev_chunk == buf.active_chunk
    assert len(buf.chunks) == 1
    assert buf.cnt_chunking == 0
    buf.may_flushing()
    assert buf.cnt_flushing == 0
    # append second, chunk flushed and new chunk created.
    buf.append("formatted data2")
    assert buf.active_chunk != prev_chunk
    assert prev_chunk.num_record == 1
    assert prev_chunk.bytesize == 15
    assert buf.active_chunk.num_record == 1
    assert buf.active_chunk.bytesize == 15
    assert len(buf.chunks) == 2
    assert buf.cnt_chunking == 1
    assert buf.cnt_flushing == 0
    buf.may_flushing()
    assert len(buf.chunks) == 1
    assert buf.cnt_flushing == 1

    # flushing by flush_interval.
    buf = MemoryBuffer(None, False, flush_interval='1s')
    assert len(buf.chunks) == 1  # initial chunk
    # append first
    prev_chunk = buf.active_chunk
    buf.append("formatted data1")
    buf.may_flushing()
    assert prev_chunk == buf.active_chunk
    assert len(buf.chunks) == 1  # no chunking yet.
    assert buf.cnt_chunking == 0
    assert buf.cnt_flushing == 0
    time.sleep(1)
    only_chunk = buf.may_flushing()
    # flushing has been occurred
    assert buf.cnt_flushing == 1
    assert buf.cnt_chunking == 1
    # new chunk has beed created since there are no chunks after flushing.
    assert only_chunk is not None
    assert buf.active_chunk != prev_chunk
    assert prev_chunk.num_record == 1
    assert buf.active_chunk.num_record == 0

    # flushing by buffer_max_chunk
    buf = MemoryBuffer(None, False, chunk_max_record=1, buffer_max_chunk=1)
    buf.append("data1")
    buf.may_flushing()
    # no chunking & flushing yet
    assert buf.cnt_chunking == 0
    assert buf.cnt_flushing == 0
    buf.append("data2")
    assert buf.cnt_chunking == 1
    buf.may_flushing()
    assert buf.cnt_flushing == 1
    assert len(buf.chunks) == 1


def test_buffer_multi(def_output):
    """Test buffer for multi data stream."""
    buf = MemoryBuffer(def_output, False, chunk_max_record=1,
                       buffer_max_chunk=1)
    buf.append("formatted data1")
    buf.append("formatted data2")
    assert buf.cnt_chunking == 1
    buf.flushing(True)
    assert len(def_output.bulks) == 2
