# swak-counter

Input plugin for Swak.
Generate incremental numbers.

## Usage

```
Usage: in.Counter [OPTIONS]

  Emit incremental number.

Options:
  --field INTEGER  Number of count fields.  [default: 1]
  --delay INTEGER  Delay seconds before next count.  [default: 1]
  --help           Show this message and exit.
```

## Sample output

```
swak run 'in.Counter --field 3'

2017-07-10 15:10:11 {"1": 1, "2": 1, "3": 1}
2017-07-10 15:10:12 {"1": 2, "2": 2, "3": 2}
2017-07-10 15:10:13 {"1": 3, "2": 3, "3": 3}
```
