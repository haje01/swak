# swak-filter

Reform plugin for Swak.
Reform events by filtering.

## Usage

Usage: ref_filter.py [OPTIONS]

  Filter events by regular expression.

Options:
  -i, --include TEXT  Key and RegExp to include.
  -x, --exclude TEXT  Key and RegExp to exclude.
  --help              Show this message and exit.

## Sample output

```
swak run 'in.Counter --count 3 | ref.'
```
