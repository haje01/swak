# swak-filter

This is a modifier plugin for Swak.
Modify events by filtering.

## Usage

Usage: mod.filter [OPTIONS]

  Filter events by regular expression.

Options:
  -i, --include TEXT  Key and RegExp to include.
  -x, --exclude TEXT  Key and RegExp to exclude.
  --help              Show this message and exit.

## Sample output

```
swak run 'in.Counter --count 3 | ref.'
```
