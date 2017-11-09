"""This module implements buffers."""

from collections import deque
import logging


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

        # If there are no left chunks, make one.
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
        # Check chunking
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
        # Check flushing
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
