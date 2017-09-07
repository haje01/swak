# swak-reform

This is a reform modifier for Swak.
Add, delete, overwrite record.

## Usage

    Usage: mod.reform [OPTIONS]

      Add, delete and modify record.

    Options:
      -a, --add <TEXT TEXT>...  Add new key / value pair.
      -d, --del TEXT            Delete existing key / value pair by key.
      --help                    Show this message and exit.

## Refer Record Value by Field Name.

You can refer the value of a field by its name. For example, if the record is `{"name": "john", "score": 100}` then `${record["name"]}` is `"john"` and `${record["score"]}` is `100`.


## Predefined Variables

You can use predefined variables in value.
There are the following predefined variables.

- `${time}` Current event's time.
- `${record["KEY"]}` Current event's record. (like dictionary)
- `${tag}` Event tag
- `${tag_parts[N]}` Refers Nth part of the seperated tag. (like zero based array)
- `${hostname}` Host name
- `${hostaddr}` Host IP address
- `${hostaddr_parts[N]}` Refers Nth part of seperated host IP address.
- `${tag_prefix[N]}`  Refers the first Nth parts of the seperated tag. (like zero based array)
- `${tag_prefix[N]}`  Refers the last Nth parts of the seperated tag. (like zero based array)

## Examples

```
    swak run 'in.counter | mod.reform -a f1_mod ${record[f1]}_mod -a host ${hostname} -a name server-${hostaddr_parts[-1]}'
```

Result:

```
["_test_", 1504687275.4991, {"host": "User.local", "f1": 1, "f1_mod": "1_mod", "name": "server-169"}]
["_test_", 1504687275.503264, {"host": "User.local", "f1": 2, "f1_mod": "2_mod", "name": "server-169"}]
["_test_", 1504687275.503934, {"host": "User.local", "f1": 3, "f1_mod": "3_mod", "name": "server-169"}]
```
