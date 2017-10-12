"""This module implements formatters."""

from datetime import datetime

import pytz


class Formatter(object):
    """Base class for formatter."""

    def __init__(self, binary, localtime=True, timezone=None,
                 time_format=None):
        """Init.

        Args:
            binary (bool): Format into binary or not.
            localtime (bool): Convert timestamp as local datetime or not.
                Defaults to True.
            timezone (str): Attach timezone to converted datetime.
            time_format (str): Time format.
        """
        self.binary = binary
        self.localtime = localtime
        self.set_timezone(timezone)
        assert timezone is not None or time_format is None or\
            ('%z' not in time_format and '%Z' not in time_format), "You need"\
            "specify timezone to use %Z or %z in format"
        self.time_format = time_format

    def set_timezone(self, timezone):
        """Set time zone.

        Args:
            timezone (str): Timezone string
        """
        if timezone is None:
            self.timezone = None
        else:
            self.timezone = pytz.timezone(timezone)

    def format(self, tag, dtime, record):
        """Format an event.

        Args:
            tag (str): Event tag.
            dtime (datetime): Event datetime.
            record (dict): Event record.
        """
        raise NotImplemented()

    def timestamp_to_datetime(self, utime):
        """Convert UTC Unix time stamp to datetime.

        Args:
            utime (float): Unix time stamp

        Returns:
            str: Datetime string.
        """
        converter = datetime.fromtimestamp if self.localtime else\
            datetime.utcfromtimestamp
        dtime = converter(utime)
        if self.timezone is not None:
            dtime = self.timezone.localize(dtime)
        if self.time_format is None:
            return dtime.isoformat()
        else:
            return dtime.strftime(self.time_format).strip()


class StdoutFormatter(Formatter):
    """Formatter class for out.stdout."""

    def __init__(self, localtime=True, timezone=None, time_format=None):
        """Init.

        Args:
            timezone (str): Timezone.
        """
        super(StdoutFormatter, self).__init__(False, localtime, timezone,
                                              time_format)

    def format(self, tag, dtime, record):
        """Format an event.

        Args:
            tag (str): Event tag
            dtime (datetime): Event datetime
            record (dict): Event record

        Returns:
            str: Formatted string
        """
        return "{dtime}\t{tag}\t{record}".format(dtime=dtime, tag=tag,
                                                 record=record)
