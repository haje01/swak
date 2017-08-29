# swak-reform

This is a reform modifier for Swak.
Add, delete, overwrite record.

## Usage

    Usage: mod.reform [OPTIONS]

      Add, delete, overwrite record.

    Options:
      -a, --add <TEXT TEXT>...  Add new key / value pair.
      -d, --del TEXT            Delete existing key / value pair by key.
      --help                    Show this message and exit.


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

    swak run 'in.counter | mod -a host "${hostname}" -a name "server-${hostaddr_parts[-1]}"'
