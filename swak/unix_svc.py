import time
import logging
from logging import config as logconfig
import traceback

import click
from daemon import Daemon

from swak.util import init_home
from swak.config import select_and_parse, get_pid_path


class SwakDaemon(Daemon):
    def run(self):
        while True:
            time.sleep(4)


@click.group()
@click.option('--home', type=click.Path(exists=True), help="Home directory.")
@click.pass_context
def cli(ctx, home):
    # select home and parse its config
    home, cfg = select_and_parse(home)
    # init required directories
    init_home(home, cfg)
    # init logger
    logconfig.dictConfig(cfg['logger'])

    # make pid_path
    pid_path = get_pid_path(home, cfg['svc_name'])
    ctx.obj['pid_path'] = pid_path


@cli.command(help="Start daemon.")
@click.pass_context
def start(ctx):
    logging.critical("========== Start daemon ==========")
    daemon = SwakDaemon(ctx.obj['pid_path'])
    daemon.start()


@cli.command(help="Stop daemon.")
@click.pass_context
def stop(ctx):
    logging.critical("========== Stop daemon ==========")
    daemon = SwakDaemon(ctx.obj['pid_path'])
    daemon.stop()


if __name__ == '__main__':
    try:
        cli(obj={})
    except Exception as e:
        for l in traceback.format_exc().splitlines():
            logging.error(l)
