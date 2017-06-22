import os
import time

import click
from daemon import Daemon


BUILD_NAME = os.environ.get('SWAK_BNAME')
BUILD_POSTFIX = "" if BUILD_NAME is None else "-{}".format(BUILD_NAME)
PID_DIR = os.path.expanduser('~/Library/Application Support/Swak')
PID_PATH = os.path.join(PID_DIR, 'swak{}.pid'.format(BUILD_POSTFIX))


class SwakDaemon(Daemon):
    def run(self):
        while True:
            time.sleep(4)


def make_pid_dir():
    if not os.path.isdir(PID_DIR):
        os.mkdir(PID_DIR)
        return True


@click.group()
def cli():
    pass


@cli.command()
def start():
    make_pid_dir()
    daemon = SwakDaemon(PID_PATH)
    daemon.start()


@cli.command()
def stop():
    daemon = SwakDaemon(PID_PATH)
    daemon.stop()


if __name__ == '__main__':
    cli()
