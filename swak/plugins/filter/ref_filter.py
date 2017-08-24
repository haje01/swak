"""Reform events by filtering."""

import re

import click

from swak.plugin import BaseReform


def make_effective_patterns(ptrns):
    """Merge & compile patterns, then return them."""
    merged = {}
    for key, regex in ptrns:
        merged[key] = regex
    result = {}
    for key, regex in merged.items():
        result[key] = re.compile(regex)
    return result


class Filter(BaseReform):
    """Filter records by regular expression."""

    def __init__(self, includes, excludes=[]):
        """Init.

        Args:
            includes (list): Regular expressions to include
            excludes (list): Regular expressions to exclude
        """
        self.includes = make_effective_patterns(includes)
        self.excludes = make_effective_patterns(excludes)

    def reform(self, tag, time, record):
        """Reform an event by filtering.

        To include, all inclusive conditions must be true,
        To exclude, one true condition is enough.
        Exclusive conditions override inclusive conditions.

        Args:
            tag (str): Event tag
            time (float): Event time
            record (dict): Event record

        Returns:
            If included
                float: Original time
                record: Original record

            If excluded
                None
        """
        if not self.includes and not self.excludes:
            return time, record

        for key, regexp in self.excludes.items():
            if key in record:
                if regexp.search(record[key]) is not None:
                    return None

        num_include = len(self.includes)
        num_match = 0
        for key, regexp in self.includes.items():
            if key not in record:
                return None
            if regexp.search(record[key]) is not None:
                num_match += 1
        if num_include == num_match:
            return time, record


@click.command(help="Filter events by regular expression.")
@click.option('-i', '--include', multiple=True, default=None,
              show_default=True, help="Key and RegExp to include.")
@click.option('-x', '--exclude', multiple=True, default=None,
              show_default=True, help="Key and RegExp to exclude.")
@click.pass_context
def main(ctx, include, exclude):
    """Entry for cli."""
    return Filter(include, exclude)


if __name__ == '__main__':
    main()
