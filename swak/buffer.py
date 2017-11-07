"""This module implements buffers."""

import time
from collections import deque
import logging

from swak.util import time_value, size_value
from swak.exception import ConfigError


class Chunk(object):
    """Chunk class."""

    def __init__(self, binary):
        """Init.

        Args:
            binary(bool): Whether store data as binary or not.
        """
        self.binary = binary
        self.reset()

    def reset(self):
        """Reset member variables."""
        self.bytesize = 0
        self.num_record = 0

    def concat(self, data, adding_size):
        """Concat new data."""
        raise NotImplementedError()

    def flush(self, output):
        """Flushing chunk into output."""
        logging.debug("Chunk.flush")
        self._flush(output)
        self.reset()

    def _flush(self, output):
        """Implement flush."""
        raise NotImplementedError()

    def empty(self):
        """Whether chunk empty or not."""
        return self.num_record == 0


class MemoryChunk(Chunk):
    """Memory chunk class."""

    def __init__(self, binary):
        """Init."""
        super(MemoryChunk, self).__init__(binary)
        self.reset()

    def reset(self):
        """Reset member variables."""
        super(MemoryChunk, self).reset()
        self.bulk = bytearray() if self.binary else []

    def concat(self, data, adding_size):
        """Concat new data."""
        logging.debug("MemoryChunk.concat adding_size {}".format(adding_size))
        if self.binary:
            self.bulk += data
        else:
            self.bulk.append(data)
        self.num_record += 1
        self.bytesize += adding_size

    def _flush(self, output):
        """Flushing chunk into output."""
        logging.debug("MemoryChunk._flush")
        output.write(self.bulk)


class DiskChunk(Chunk):
    """Disk chunk class."""


class Buffer(object):
    """Base class for buffer."""

    def __init__(self, output, memory, binary, flush_at_shutdown):
        """Init.

        Args:
            output (Output): An output.
            memory (bool): Store data to memory or disk.
            binary (bool): Store data as binary or not.
        """
        self.output = output
        self.memory = memory
        self.binary = binary
        self.tag = None
        initial_chunk = self.new_chunk()
        self.chunks = deque([initial_chunk])
        self.last_flush = None
        self.cnt_flushing = 0
        self.cnt_chunking = 0
        self.started = None
        self.flush_at_shutdown = flush_at_shutdown

    def set_tag(self, tag):
        """Set tag."""
        self.tag = tag

    @property
    def empty(self):
        """All chunks empty or not."""
        for chunk in self.chunks:
            if not chunk.empty:
                return False
        return True

    @property
    def active_chunk(self):
        """Return active chunk."""
        assert len(self.chunks) > 0
        return self.chunks[-1]

    @property
    def num_chunk(self):
        """Return number of chunks."""
        return len(self.chunks)

    def start(self):
        """Start buffer."""
        assert not self.started
        self.started = True

    def stop(self):
        """Stop buffer."""
        assert self.started
        self.started = False

    def append(self, data):
        """Append data stream to buffer.

        If matches flush condition, will call ``flush`` with chunk

        Args:
            data: Formatted event.

        Returns:
            int: Adding size of data.
        """
        raise NotImplementedError()

    def chunking(self):
        """Create new chunk and append.

        Returns:
            Chunk: Created chunk.
        """
        logging.debug("Buffer.chunking")
        new_chunk = self.new_chunk()
        self.chunks.append(new_chunk)
        self.cnt_chunking += 1
        return new_chunk

    def flushing(self, flush_all=False):
        """Pop chunk and flush it.

        If no remain chunks, create one and return it.

        Args:
            flush_all (bool): Whether flush all or just one.

        Returns:
            Chunk: Chunk created after flushing.
        """
        logging.debug("Buffer.flushing")
        while True:
            try:
                head_chunk = self.chunks.popleft()
                if self.output is not None:
                    head_chunk.flush(self.output)
                self.cnt_flushing += 1
                if not flush_all:
                    break
            except IndexError:
                break

        # if there are no left chunks, make one.
        if self.num_chunk == 0:
            logging.debug("no more chunk, make one")
            return self.chunking()

    def may_chunking(self, adding_size):
        """Chunking if needed.

        If new chunk is need for new data, make one.

        Args:
            adding_size (int): New data size in bytes.

        Returns:
            Chunk: Active chunk.
        """
        logging.debug("may_chunking adding_size {}".format(adding_size))
        active_chunk = self.active_chunk
        new_chunk = None
        # check chunking
        if self.need_chunking(adding_size):
            logging.debug("need chunk, make one")
            new_chunk = self.chunking()
            active_chunk = new_chunk

        return active_chunk

    def may_flushing(self, last_flush_interval=None):
        """Flushing if needed.

        Args:
            last_flush_interval (float): Force flushing interval when input
              is terminated.

        Returns:
            Chunk: Chunk created after flushing.
        """
        # check flushing
        logging.debug("may_flushing")
        if self.need_flushing(last_flush_interval):
            return self.flushing()

    def new_chunk(self):
        """New chunk."""
        if self.memory:
            return MemoryChunk(self.binary)
        else:
            return DiskChunk(self.binary)

    def need_chunking(self):
        """Need new chunk or not."""
        raise NotImplementedError()

    def need_flushing(self, last_flush_interval):
        """Need flushing or not.

        Args:
            last_flush_interval (float): Force flushing interval for input
              is terminated.
        """
        raise NotImplementedError()


class MemoryBuffer(Buffer):
    """Buffer which store its chunks in memory."""

    def __init__(self, output, binary, chunk_max_record=None,
                 buffer_max_chunk=64, chunk_max_size='64m',
                 flush_interval=None):
        """Init.

        Args:
            output (Output): An output.
            binary (bool): Store data as binary or not.
            chunk_max_record (int): Maximum records per chunk for slicing.
            buffer_max_chunk (int): Maximum chunks per buffer for slicing.
            chunk_max_size (str): Maximum chunk size for slicing with suffix.
            flush_interval (str): Flush interval with time suffix.
        """
        super(MemoryBuffer, self).__init__(output, True, binary, True)

        assert type(chunk_max_size) is str, "chunk_max_size must be a string."
        assert flush_interval is None or type(flush_interval) is str,\
            "flush_interval must be a string."

        try:
            chunk_max_size = size_value(chunk_max_size)
            flush_interval = time_value(flush_interval)
        except ValueError as e:
            raise ConfigError(str(e))

        # validate arguements.
        if chunk_max_record is not None and chunk_max_record <= 0:
            raise ConfigError("chunk_max_record must be greater than 0.")
        if buffer_max_chunk is not None and buffer_max_chunk <= 0:
            raise ConfigError("buffer_max_chunk must be greater than 0.")
        if chunk_max_size is not None and chunk_max_size <= 0:
            raise ConfigError("chunk_max_size must be greater than 0.")
        if flush_interval is not None and flush_interval <= 0:
            raise ConfigError("flush_interval must be greater than 0.")

        self.chunk_max_record = chunk_max_record
        self.chunk_max_size = chunk_max_size
        self.buffer_max_chunk = buffer_max_chunk
        self.flush_interval = flush_interval

        self.queue = None
        self.max_record = 0

    def set_max_record(self, max_record):
        """Set maximum records number."""
        self.max_record = max_record

    def append(self, data, binary_data=False):
        """Append data stream to buffer.

        Args:
            data (bytearray or str) bytearry if this is a binary buffer,
              otherwise string data.
            binary_data (bool): Whether this data is already binarized or not.

        Returns:
            int: Adding size of data.
        """
        logging.debug("MemoryBuffer.append")
        bytedata = data if binary_data else bytearray(data, encoding='utf8')
        adding_size = len(bytedata)
        if self.binary:
            data = bytedata

        chunk = self.may_chunking(adding_size)
        chunk.concat(data, adding_size)
        return adding_size

    def need_chunking(self, adding_size):
        """Need new chunk or not.

        Args:
            adding_size (int): New data size in bytes.
        """
        chunk = self.active_chunk
        if self.chunk_max_record is not None and chunk.num_record + 1 >\
                self.chunk_max_record:
            return True
        if self.chunk_max_size is not None and chunk.bytesize + adding_size >\
                self.chunk_max_size:
            return True

    def need_flushing(self, last_flush_interval):
        """Need flushing or not.

        Flush with the following conditions:
        - if number of chunk is greater than buffer max chunk.
        - if flush interval has passed.
        - if last flush interval has passed.

        Args:
            last_flush_interval (float): Force flushing interval for input
              is terminated.
        """
        if len(self.chunks) > self.buffer_max_chunk:
            # force flushing to remove head chunk.
            return True
        cur = time.time()
        if self.last_flush is None:
            self.last_flush = time.time()
        diff = cur - self.last_flush
        if self.flush_interval is not None and diff >= self.flush_interval:
            self.last_flush = cur
            return True
        if last_flush_interval is not None and diff >=\
                last_flush_interval:
            self.last_flush = cur
            return True
