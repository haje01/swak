"""This module implements plugin base."""

import time
import logging
from logging import config as logconfig
import traceback

import click
from daemon import Daemon

from swak.util import init_home, check_python_version
from swak.config import select_and_parse, get_pid_path
from swak.cli import main


check_python_version()


class SwakDaemon(Daemon):
    """Daemon class."""

    def run(self):
        """Daemon main."""
        while True:
            time.sleep(4)


@main.group(help="Unix daemon commands.")
@click.option('--home', type=click.Path(exists=True), help="Home directory.")
@click.pass_context
def daemon(ctx, home):
    """Daemon CLI entry."""
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


@daemon.command(help="Start daemon.")
@click.pass_context
def start(ctx):
    """Daemon start."""
    logging.critical("========== Start daemon ==========")
    daemon = SwakDaemon(ctx.obj['pid_path'])
    daemon.start()


@daemon.command(help="Stop daemon.")
@click.pass_context
def stop(ctx):
    """Daemon stop."""
    logging.critical("========== Stop daemon ==========")
    daemon = SwakDaemon(ctx.obj['pid_path'])
    daemon.stop()


if __name__ == '__main__':
    try:
        main(obj={})
    except Exception as e:
        for l in traceback.format_exc().splitlines():
            logging.error(l)
