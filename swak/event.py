"""Event."""


class EventStream(object):
    """EventStream class."""

    def __init__(self):
        """init."""
        super(EventStream, self).__init__()


class OneEventStream(EventStream):
    """EventStream class."""

    def __init__(self, time, record):
        """init.

        Args:
            time (float): emit time.
            record (dict): record to emit.
        """
        super(OneEventStream, self).__init__()
        self.time = time
        self.record = record

    def __iter__(self):
        """Return iterator."""
        self.iter_n = 0
        return self

    def __next__(self):
        """Iterate next."""
        if self.iter_n == 0:
            self.iter_n += 1
            return self.time, self.record
        raise StopIteration()


# class ArrayEventStream(EventStream):
#     """EventStream class."""

#     def __init__(self, entries):
#         """init."""
#         super(ArrayEventStream, self).__init__()
#         self.entries = entries

#     def __iter__(self):
#         """Return iterator."""
#         self.iter_n = 0
#         self.iter_max = len(self.entries)
#         return self

#     def __next__(self):
#         """Iterate next."""
#         if self.iter_n <= self.iter_max:
#             result = self.entries[self.n]
#             self.iter_n += 1
#             return result
#         else:
#             raise StopIteration()


class MultiEventStream(EventStream):
    """MultiEventStream class."""

    def __init__(self, times=[], records=[]):
        """init."""
        super(MultiEventStream, self).__init__()
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
            time, record = self.times[self.iter_n], self.records[self.iter_n]
            self.iter_n += 1
            return time, record
        else:
            raise StopIteration()
