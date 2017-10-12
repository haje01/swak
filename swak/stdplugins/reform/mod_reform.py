from __future__ import absolute_import  # NOQA
"""This module implements modifier plugin of reform."""

import re
import socket

import click
from six import string_types

from swak.plugin import Modifier

# Syntax patterns
ptrn_tag_parts = re.compile(r'{tag_parts\[(-?\d)\]}')
ptrn_hostaddr_parts = re.compile(r'{hostaddr_parts\[(-?\d)\]}')
ptrn_variable = re.compile(r'\$\{([^}]+?)\}')
ptrn_curly_bracket = re.compile(r'([^\$]|^)\{([^}]+?)\}')


def _tag_prefix(tag_parts):
    cnt = len(tag_parts)
    if cnt == 0:
        return []
    tag_prefix = [None] * cnt
    for i in range(1, cnt + 1):
        tag_prefix[i - 1] = '.'.join([tag_parts[j] for j in range(0, i)])
    return tag_prefix


def _tag_suffix(tag_parts):
    cnt = len(tag_parts)
    if cnt == 0:
        return []
    rev_tag_parts = tag_parts[::-1]
    rev_tag_suffix = [None] * cnt
    for i in range(1, cnt + 1):
        rev_tag_suffix[i - 1] = '.'.join([rev_tag_parts[j]
                                         for j in range(0, i)][::-1])
    return rev_tag_suffix


def _normalize(expr):
    """Normalize value expression.

    Normalize value expression for python string formatting.

    - {lit} -> {{lit}}
    - ${val} -> {val}

    Args:
        expr (str): Value expression

    Returns:
        str: Formalized string
    """
    expr = ptrn_variable.sub('%[%[\\1%]%]', expr)
    expr = expr.replace('{', '{{').replace('}', '}}')
    return expr.replace('%[%[', '{').replace('%]%]', '}')


def _expand(val, placeholders):
    """Expand value string with placeholders.

    Args:
        val (str): A string value with possible placeholder.
        placeholders (dict): Placeholder value reference.

    Returns:
        dict: Expanded value
    """
    # expand tag_parts
    while True:
        m = ptrn_tag_parts.search(val)
        if m is None:
            break
        idx = int(m.groups()[0])
        key = '{{tag_parts[{}]}}'.format(idx)
        phv = placeholders[key]
        val = val.replace(key, phv)

    # expand hostaddr_parts
    while True:
        m = ptrn_hostaddr_parts.search(val)
        if m is None:
            break
        idx = int(m.groups()[0])
        key = '{{hostaddr_parts[{}]}}'.format(idx)
        phv = placeholders[key]
        val = val.replace(key, phv)

    return val.format(**placeholders)


def _make_default_placeholders():
    """Make a default placeholder."""
    pholder = {}
    hostname = socket.gethostname()
    pholder['hostname'] = hostname
    hostaddr = socket.gethostbyname(hostname)
    pholder['hostaddr'] = hostaddr
    hostaddr_parts = hostaddr.split('.')
    for i in range(4):
        key = '{{hostaddr_parts[{}]}}'.format(i)
        pholder[key] = hostaddr_parts[i]
        rkey = '{{hostaddr_parts[{}]}}'.format(i - 4)
        pholder[rkey] = hostaddr_parts[i]
    return pholder


class Reform(Modifier):
    """Reform class."""

    def __init__(self, writes, deletes=[]):
        """Init.

        Args:
            writes (list): List of (key, value) tuple to add.
            deletes (list): List of key to delete.
        """
        for k, v in writes:
            assert isinstance(k, string_types), "Key must be a string"
            assert isinstance(k, string_types), "Value must be a string"
        self.writes = writes
        self.deletes = deletes

    def prepare_for_stream(self, tag, es):
        """Prepare to modify an event stream.

        Args:
            tag (str): Event tag
            es (EventStream): Event stream
        """
        placeholders = _make_default_placeholders()
        placeholders['tag'] = tag
        tag_parts = tag.split('.')
        tp_cnt = len(tag_parts)

        # tag parts
        placeholders['tag_parts'] = tag_parts
        for i in range(tp_cnt):
            key = '{{tag_parts[{}]}}'.format(i)
            placeholders[key] = tag_parts[i]
            rkey = '{{tag_parts[{}]}}'.format(i - tp_cnt)
            placeholders[rkey] = tag_parts[i]

        placeholders['tag_prefix'] = _tag_prefix(tag_parts)
        placeholders['tag_suffix'] = _tag_suffix(tag_parts)
        self.placeholders = placeholders

    def modify(self, tag, utime, record):
        """Modify an event by modifying.

        If adds & dels conflicts, deleting key wins.

        Args:
            tag (str): Event tag
            utime (float): Event time stamp.
            record (dict): Event record

        Returns:
            float: Modified time
            record: Modified record
        """
        assert type(record) is dict
        self.placeholders['time'] = utime
        self.placeholders['record'] = record
        for key, val in self.writes:
            record[key] = _expand(_normalize(val), self.placeholders)

        for key in self.deletes:
            del record[key]

        return utime, record


@click.command(help="Write or delete record fields.")
@click.option('-w', '--write', "writes", type=(str, str), multiple=True,
              help="Write key / value pair.")
@click.option('-d', '--delete', "deletes", type=str, multiple=True,
              help="Delete existing key / value pair by key.")
def main(writes, deletes):
    """Plugin entry."""
    return Reform(writes, deletes)


if __name__ == '__main__':
    main()
