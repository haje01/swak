"""This module implements formatters."""

from datetime import datetime

import pytz


class Formatter(object):
    """Base class for formatter."""

    def __init__(self, binary, timezone='UTC'):
        """Init.

        Args:
            binary (bool): Format into binary or not.
            timezone (str): Timezone. refer
                https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
        """
        self.binary = binary
        self.timezone = pytz.timezone(timezone)

    def format(self, tag, time, record):
        """Format an event.

        Args:
            tag (str): Event tag
            time (float): Event timestamp
            record (dict): Event record
        """
        raise NotImplemented()


class StdoutFormatter(Formatter):
    """Formatter class for out.stdout."""

    def __init__(self, timezone='UTC'):
        """Init.

        Args:
            timezone (str): Timezone.
        """
        super(StdoutFormatter, self).__init__(False, timezone)

    def format(self, tag, time, record):
        """Format an event.

        Args:
            tag (str): Event tag
            time (float): Event timestamp
            record (dict): Event record

        Returns:
            str: Formatted string
        """
        dtime = self.timezone.localize(datetime.fromtimestamp(time))
        return "{dtime}\t{tag}\t{record}".format(dtime=dtime, tag=tag,
                                                 record=record)
