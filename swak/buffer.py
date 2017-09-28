"""This module implements buffers."""

import time
from collections import deque

from swak.util import time_value, size_value


class Chunk(object):
    """Chunk class."""

    def __init__(self, binary):
        """Init.

        Args:
            binary(bool): Whether store data as binary or not.
        """
        self.binary = binary
        self.total_bytes = 0
        self.num_record = 0

    @property
    def bytesize(self):
        """Return chunk size in byte."""
        assert self.binary, "Require data in binary format."
        return self.total_bytes

    def concat(self, data, adding_size):
        """Concat new data."""
        raise NotImplementedError()

    def flush(self, output):
        """Flushing chunk into output."""
        raise NotImplementedError()


class MemoryChunk(Chunk):
    """Memory chunk class."""

    def __init__(self, binary):
        """Init."""
        super(MemoryChunk, self).__init__(binary)
        self.bulk = bytearray() if binary else []

    def concat(self, data, adding_size):
        """Concat new data."""
        if self.binary:
            self.bulk += data
        else:
            self.bulk.append(data)

    def flush(self, output):
        """Flushing chunk into output."""
        bulk = self.bulk if self.binary else ''.join(self.bulk)
        output.write(bulk)


class DiskChunk(Chunk):
    """Disk chunk class."""


class Buffer(object):
    """Base class for buffer."""

    def __init__(self, output, memory, binary):
        """Init.

        Args:
            output (Output): An output.
            memory (bool): Store data to memory or not. (=disk)
            binary (bool): Store data as binary or not.
        """
        self.output = output
        self.memory = memory
        self.binary = binary
        self.tag = None
        self.num_flush = 0
        initial_chunk = self.new_chunk()
        self.chunks = deque([initial_chunk])

    def set_tag(self, tag):
        """Set tag."""
        self.tag = tag

    @property
    def num_chunk(self):
        """Return number of chunks."""
        return len(self.chunks)

    def append(self, data):
        """Append event stream to buffer.

        If matches flush condition, will call ``flush`` with chunk

        Args:
            data: a formatted event.
        """
        raise NotImplementedError()

    def check_flush_and_new_chunk(self, output, adding_size):
        """Check to flush and new chunk.

        If need to flush chunk, flush head chunk and append new chunk to tail.
        Otherwise, return current tail chunk

        Args:
            output (Output)
            adding_size (int): New byte size to add to chunk.
        """
        if self.need_flush(adding_size):
            # flush & pop head chunk and append new chunk.
            head_chunk = self.chunks.popleft()
            head_chunk.flush(self.output)
            new_chunk = self.new_chunk()
            self.chunks.append(new_chunk)
            return new_chunk
        else:
            return self.chunks[-1]

    def new_chunk(self):
        """New chunk."""
        if self.memory:
            return MemoryChunk(self.binary)
        else:
            return DiskChunk(self.binary)

    def need_flush(self, adding_size):
        """Test if need to flush or not.

        Args:
            adding_size (int): New byte size to add to chunk.
        """
        raise NotImplementedError()


class SizedBuffer(Buffer):
    """Buffer class in which chunks are sliced by size."""

    def __init__(self, output, memory, binary, chunk_max_record,
                 chunk_max_size, buffer_max_chunk, buffer_max_size,
                 flush_interval):
        """Init.

        Args:
            output (Output): An output.
            memory (bool): Store data to memory or not. (=disk)
            binary (bool): Store data as binary or not.
            chunk_max_record (int): Maximum records per chunk for slicing.
            chunk_max_size (str): Maximum chunk size for slicing with suffix.
            buffer_max_chunk (int): Maximum chunks per buffer for slicing.
            buffer_max_size (str): Maximum buffer size for slicing with suffix.
            flush_interval (str): Flush interval with time suffix.
        """
        super(SizedBuffer, self).__init__(output, memory, binary)

        # validate argument
        if not binary and (chunk_max_size is not None or buffer_max_size is not
                           None):
            raise ValueError("Size arguments needs binary format.")

        self.chunk_max_record = chunk_max_record
        self.chunk_max_size = size_value(chunk_max_size)
        self.buffer_max_chunk = buffer_max_chunk
        self.buffer_max_size = size_value(buffer_max_size)
        self.flush_interval = time_value(flush_interval)

        self.queue = None
        self.max_record = 0

    def set_max_record(self, max_record):
        """Set maximum records number."""
        self.max_record = max_record

    def append(self, data):
        """Append event stream to buffer.

        Args:
            data: a formatted event.
        """
        adding_size = 0
        if self.binary:
            data = bytearray(data, encoding='utf8')
            adding_size += len(data)

        chunk = self.check_flush_and_new_chunk(self.output, adding_size)
        chunk.concat(data, adding_size)

    def need_flush(self, adding_size):
        """Test if need to flush or not.

        Args:
            adding_size (int): New byte size to add to chunk.
        """
        chunk = self.chunks[-1]
        if self.chunk_max_record is not None and chunk.num_record + 1 >=\
                self.chunk_max_record:
            return True
        if self.chunk_max_size is not None and chunk.bytesize + adding_size >=\
                self.chunk_max_size:
            return True
        if self.buffer_max_chunk is not None and len(self.chunks) + 1 >\
                self.buffer_max_chunk:
            return True
        if self.buffer_max_size is not None and self.chunks_total_size +\
                adding_size >= self.buffer_max_size:
            return True
        if self.flush_interval is not None and self.last_flush - time.time()\
                >= self.flush_interval:
            return True


# @click.command(help="Buffering by size sliced chunk.")
# @click.option('-r', '--chunk-max-record', default=None, type=int,
#               help="Maximum records per chunk for slicing.")
# @click.option('-s', '--chunk-max-size', default='8m', show_default=True,
#               help="Maximum chunk size for slicing.")
# @click.option('-c', '--buffer-max-chunk', default=64, show_default=True,
#               help="Maximum chunks per buffer for slicing.")
# @click.option('-b', '--buffer-max-size', default='512m', show_default=True,
#               help="Maximum buffer size for slicing.")
# @click.option('-i', '--flush-interval', default='60s', show_default=True,
#               help="Flushing interval.")
# @click.pass_context
# def main(ctx, binary, chunk_max_record, chunk_max_size, buffer_max_chunk,
#          buffer_max_size, flush_interval):
#     """Plugin entry."""
#     return Sized(binary, chunk_max_record, chunk_max_size, buffer_max_chunk,
#                  buffer_max_size, flush_interval)


# if __name__ == '__main__':
#     main()
