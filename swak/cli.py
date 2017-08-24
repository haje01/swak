"""Swak command line interface."""

from __future__ import print_function

import sys
import logging

import click
from tabulate import tabulate

from swak.util import check_python_version, set_log_verbosity
from swak.plugin import enumerate_plugins, check_plugins_initpy

check_python_version()


@click.group()
@click.option('-v', '--verbose', count=True, help="Increase verbosity.")
@click.pass_context
def main(ctx, verbose):
    """Entry for CLI."""
    ctx.obj['verbosity'] = verbose


if not getattr(sys, 'frozen', False):
    @main.command(help="Search and update plugin information.")
    @click.pass_context
    def refresh(ctx):
        """Refresh plugin infomations."""
        verbosity = ctx.obj['verbosity']
        set_log_verbosity(verbosity)
        check_plugins_initpy(enumerate_plugins())


@main.command(help="List known plugins.")
@click.pass_context
def list(ctx):
    """List known plugins."""
    plugins = prepare_cli(ctx)

    mmap = plugins.MODULE_MAP
    cnt = len(mmap)
    mnames = sorted(mmap.keys())
    plugins = []
    for mname in mnames:
        desc = mmap[mname].main.help
        info = [mname, desc]
        plugins.append(info)

    print("Swak has {} plugin(s):".format(cnt))
    header = ['Plugin', 'Description']
    print(tabulate(plugins, headers=header, tablefmt='psql'))


@main.command(help="Show help message for a plugin.")
@click.argument('plugin')
@click.pass_context
def desc(ctx, plugin):
    """Show help message for a plugin."""
    plugins = prepare_cli(ctx)

    mmap = plugins.MODULE_MAP
    if plugin in mmap:
        mmap[plugin].main(args=['--help'])
    else:
        print("Can not find plugin '{}'".format(plugin), file=sys.stderr)


@main.command(help="Run commands for test.")
@click.argument('commands')
@click.pass_context
def run(ctx, commands):
    """Run commands for test."""
    pass
    # handle_command_options(ctx)
    # parse_and_run_test_cmds(commands)


def prepare_cli(ctx):
    """Prepare cli command execution.

    - set log level by verbosity
    - import plugins by load plugins/__init__.py module

    Returns:
        module: plugins/__init__.py module
    """
    verbosity = ctx.obj['verbosity']
    set_log_verbosity(verbosity)

    try:
        import swak.plugins
        swak.plugins.MODULE_MAP  # sanity check
    except Exception as e:
        print("Plugin information not exists. Try `refresh`.")
        logging.error(str(e))
        sys.exit(-1)
    else:
        return swak.plugins
