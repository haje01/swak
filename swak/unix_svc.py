import time
import logging
from logging import config as logconfig
import traceback

import click
from daemon import Daemon

from swak.util import init_home
from swak.config import select_and_parse, get_pid_path
from swak.test import _run as test_run


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

    ctx.obj['home'] = home
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


@cli.command(help="Test in no daemon mode.")
@click.option('--task', type=int, default=1, show_default=True, help="Task number to test.")
@click.option('--version', is_flag=True, help="Show Swak version.")
@click.pass_context
def test(ctx, task, version):
    home = ctx.obj['home']
    test_run(home, task, version)


if __name__ == '__main__':
    try:
        cli(obj={})
    except Exception as e:
        for l in traceback.format_exc().splitlines():
            logging.error(l)
