"""This module implements data stream classes."""


class DataStream(object):
    """DataStream class."""

    def __init__(self):
        """init."""
        super(DataStream, self).__init__()

    def __len__(self):
        """Length of data."""
        raise NotImplementedError()

    def empty(self):
        """Wheter stream is empty."""
        return len(self) == 0


class OneDataStream(DataStream):
    """DataStream class."""

    def __init__(self, utime, record):
        """init.

        Args:
            utime (float): emit time stamp.
            record (dict): record to emit.
        """
        super(OneDataStream, self).__init__()
        self.utime = utime
        assert type(record) is dict
        self.record = record

    def __iter__(self):
        """Return iterator."""
        self.iter_n = 0
        return self

    def __next__(self):
        """Iterate next."""
        if self.iter_n == 0:
            self.iter_n += 1
            return self.utime, self.record
        raise StopIteration()

    def next(self):
        """Iterate next for Python2."""
        return self.__next__()

    def __len__(self):
        """Length of datas."""
        return 1


class MultiDataStream(DataStream):
    """MultiDataStream class."""

    def __init__(self, times=[], records=[]):
        """init."""
        super(MultiDataStream, self).__init__()
        assert len(times) == len(records)
        self.times = times
        self.records = records

    def __iter__(self):
        """Return iterator."""
        self.iter_n = 0
        self.iter_max = len(self.times)
        return self

    def __next__(self):
        """Iterate next."""
        if self.iter_n < self.iter_max:
            utime, record = self.times[self.iter_n], self.records[self.iter_n]
            self.iter_n += 1
            return utime, record
        else:
            raise StopIteration()

    def next(self):
        """Iterate next for Python2."""
        return self.__next__()

    def __len__(self):
        """Length of data."""
        return len(self.records)
