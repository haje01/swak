"""This module implements buffers."""

import time
import logging

from six import string_types

from swak.buffer import Buffer
from swak.util import time_value, size_value
from swak.exception import ConfigError


DEFAULT_CHUNK_MAX_RECORD = 1000
DEFAULT_CHUNK_MAX_SIZE = '4m'
DEFAULT_BUFFER_MAX_CHUNK = 4


class MemoryBuffer(Buffer):
    """Buffer which store its chunks in memory."""

    def __init__(self, output, binary,
                 chunk_max_record=DEFAULT_CHUNK_MAX_RECORD,
                 chunk_max_size=DEFAULT_CHUNK_MAX_SIZE,
                 buffer_max_chunk=DEFAULT_BUFFER_MAX_CHUNK,
                 flush_interval=None):
        """Init.

        Args:
            output (Output): An output.
            binary (bool): Store data as binary or not.
            chunk_max_record (int): Maximum records per chunk for slicing.
            chunk_max_size (str): Maximum chunk size for slicing with suffix.
            buffer_max_chunk (int): Maximum chunks per buffer for slicing.
            flush_interval (str): Flush interval with time suffix.
        """
        super(MemoryBuffer, self).__init__(output, True, binary, True)

        assert isinstance(chunk_max_size, string_types), "chunk_max_size must"\
            " be a string."
        assert flush_interval is None or \
            isinstance(flush_interval, string_types),\
            "flush_interval must be a string."

        try:
            chunk_max_size = size_value(chunk_max_size)
            flush_interval = time_value(flush_interval)
        except ValueError as e:
            raise ConfigError(str(e))

        # Validate arguements.
        if chunk_max_record is not None and chunk_max_record <= 0:
            raise ConfigError("chunk_max_record must be greater than 0..")
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

        logging.info("MemoryBuffer.__init__- chunk_max_record {}, "
                     "chunk_max_size {}, buffer_max_chunk {}, "
                     "flush_interval {}".format(chunk_max_record,
                                                chunk_max_size,
                                                buffer_max_chunk,
                                                flush_interval))

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
            # Force flushing to remove head chunk.
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
