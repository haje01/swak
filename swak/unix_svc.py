import os
import time
import logging
from logging import config as logconfig
import traceback

import click
from daemon import Daemon

from swak.util import query_pid_path, init_home_dirs
from swak.config import select_and_parse


class SwakDaemon(Daemon):
    def run(self):
        while True:
            time.sleep(4)


@click.group()
@click.option('--config', type=click.Path(exists=True), help="Config file"
              " path.")
@click.pass_context
def cli(ctx, config):
    cfg = select_and_parse(config)
    # init required directories
    init_home_dirs(cfg)
    # init logger
    logconfig.dictConfig(cfg['logger'])

    # make pid_path
    svc_name = cfg['svc_name']
    pid_path = query_pid_path(svc_name)
    ctx.obj['pid_path'] = pid_path


@cli.command(help="Start daemon.")
@click.pass_context
def start(ctx):
    logging.critical("========== Start daemon ==========")
    cfg = select_and_parse()
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
