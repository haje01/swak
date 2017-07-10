from __future__ import print_function

import click

from swak.plugin import BaseOutput


class Stdout(BaseOutput):

    def process(self, record):
        print(record)


@click.command(help="Output to standard output.")
def main():
    return Stdout()


if __name__ == '__main__':
    main()
