# swak-counter

An input plugin for Swak.
Generate incremental numbers.

## Usage

```
Usage: in.counter [OPTIONS]

  Generate incremental numbers.

Options:
  -c, --count INTEGER  Count to emit.  [default: 3]
  -f, --field INTEGER  Count of fields.  [default: 1]
  -d, --delay FLOAT    Delay seconds before next count.  [default: 0.0]
  --help               Show this message and exit
```

## Sample output

```
swak run 'in.counter --field 4 --delay 1'

time: 1504684228.58914, record: {'f3': 1, 'f4': 1, 'f1': 1, 'f2': 1}
time: 1504684229.592921, record: {'f3': 2, 'f4': 2, 'f1': 2, 'f2': 2}
time: 1504684230.593845, record: {'f3': 3, 'f4': 3, 'f1': 3, 'f2': 3}
```
