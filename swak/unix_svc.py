import os
import time

import click
from daemon import Daemon

from swak.util import query_pid_path


build_name = os.environ.get('SWAK_BNAME')
build_postfix = "" if build_name is None else "-{}".format(build_name)
pid_path = query_pid_path(build_postfix)


class SwakDaemon(Daemon):
    def run(self):
        while True:
            time.sleep(4)


@click.group()
def cli():
    pass


@cli.command()
def start():
    daemon = SwakDaemon(pid_path)
    daemon.start()


@cli.command()
def stop():
    daemon = SwakDaemon(pid_path)
    daemon.stop()


if __name__ == '__main__':
    cli()
