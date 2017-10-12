"""This module implements formatter test."""
from __future__ import absolute_import

import time
from datetime import datetime

from swak.formatter import Formatter, StdoutFormatter

UTIME = 1506650186.31426
DTIME = '2017-09-29T10:56:26.314260'


def test_formatter_basic():
    """Test basic formatter features."""
    # time stamp to datetime
    fmt = Formatter(False, True)
    utime = time.time()
    dtime = fmt.timestamp_to_datetime(UTIME)
    assert DTIME == dtime

    # format
    fmt = StdoutFormatter(True, None)
    assert '2017-09-29T10:56:26.314260\ttest\t{}' ==\
        fmt.format('test', DTIME, {})

    fmt = StdoutFormatter(True, 'UTC')
    dtime = fmt.timestamp_to_datetime(utime)
    assert '+00:00' in fmt.format('test', dtime, {})

    fmt = StdoutFormatter(True, 'Asia/Seoul')
    dtime = fmt.timestamp_to_datetime(utime)
    assert '+09:00' in fmt.format('test', dtime, {})

    # time format
    fmt = StdoutFormatter(None, None, '%Y%m%d/%H')
    assert '20170929/01' == fmt.timestamp_to_datetime(UTIME)
    fmt = StdoutFormatter(None, 'Asia/Seoul', '%Y%m%d/%H %z')
    assert '20170929/01 +0900' == fmt.timestamp_to_datetime(UTIME)
