"""This module implements command line interface."""

from __future__ import print_function

import sys
import logging

import click
from tabulate import tabulate

from swak.util import check_python_version, set_log_verbosity
from swak.plugin import enumerate_plugins, check_plugins_initpy, PREFIX,\
    get_plugins_dir, init_plugin_dir
from swak.core import parse_and_validate_test_cmds, run_test_cmds

check_python_version()

INIT_PREFIX = [p for p in PREFIX]
PLUGIN_DIR = get_plugins_dir(False)


@click.group()
@click.option('-v', '--verbose', count=True, help="Increase verbosity.")
@click.pass_context
def main(ctx, verbose):
    """Entry for CLI."""
    ctx.obj['verbosity'] = verbose


# if not packeged into binary
if not getattr(sys, 'frozen', False):
    # provide refresh command
    @main.command(help="Search and update plugin information.")
    @click.option('-f', '--force', is_flag=True, help="Remove existing "
                  "information and refresh again.")
    @click.pass_context
    def refresh(ctx, force):
        """Refresh plugin infomations."""
        verbosity = ctx.obj['verbosity']
        set_log_verbosity(verbosity)
        _refresh(force)


def _refresh(force=False):
    check_plugins_initpy(True, enumerate_plugins(True), force)
    check_plugins_initpy(False, enumerate_plugins(False), force)


@main.command(help='Init new plugin package.')
@click.option('-t', '--type', "ptypes", type=click.Choice(INIT_PREFIX),
              default="mod", show_default=True, multiple=True,
              help="Plugin module type prefix.")
@click.option('-d', '--dir', 'pdir', type=click.Path(exists=True),
              default=PLUGIN_DIR, show_default=True, help="Plugin directory")
@click.argument('file_name')
@click.argument('class_name')
@click.pass_context
def init(ctx, ptypes, pdir, file_name, class_name):
    """Init new plugin package."""
    init_plugin_dir(ptypes, file_name, class_name, pdir)


@main.command(help="List known plugins.")
@click.option('-r', '--refresh', is_flag=True, help="Refresh first then list.")
@click.pass_context
def list(ctx, refresh):
    """List known plugins."""
    if refresh:
        _refresh()
    stdex_plugins = prepare_cli(ctx)

    for i in range(2):  # standard / external plugins
        mmap = stdex_plugins[i].MODULE_MAP
        cnt = len(mmap)
        mnames = sorted(mmap.keys())
        plugins = []
        for mname in mnames:
            desc = mmap[mname].main.help
            info = [mname, desc]
            plugins.append(info)

        if i == 0:
            print("Swak has {} standard plugins:".format(cnt))
        else:
            print("And {} external plugin(s):".format(cnt))
        header = ['Plugin', 'Description']
        print(tabulate(plugins, headers=header, tablefmt='psql'))


@main.command(help="Show help message for a plugin.")
@click.argument('plugin')
@click.pass_context
def desc(ctx, plugin):
    """Show help message for a plugin.

    Args:
        plugin (str): Plugin name with prefix
    """
    plugins = prepare_cli(ctx)

    for i in range(2):  # standard / external plugins
        mmap = plugins[i].MODULE_MAP
        if plugin in mmap:
            sys.argv[0] = plugin
            mmap[plugin].main(args=['--help'])
            return

    print("Can not find plugin '{}'".format(plugin), file=sys.stderr)


@main.command(help="Run '|' seperated test commands.")
@click.argument('commands')
@click.pass_context
def run(ctx, commands):
    """Run commands for test.

    Args:
        commands (str): Test commands concated with '|'
    """
    cmds = parse_and_validate_test_cmds(commands)
    run_test_cmds(cmds)


def prepare_cli(ctx):
    """Prepare cli command execution.

    - set log level by verbosity
    - import plugins by load plugins/__init__.py module

    Returns:
        module: stdplugins/__init__.py module
        module: plugins/__init__.py module
    """
    verbosity = ctx.obj['verbosity']
    set_log_verbosity(verbosity)

    try:
        import swak.stdplugins
        swak.stdplugins.MODULE_MAP  # sanity check

        import swak.plugins
        swak.plugins.MODULE_MAP  # sanity check
    except Exception as e:
        print("Plugin information not exists. Try `refresh`.")
        logging.error(str(e))
        sys.exit(-1)
    else:
        return (swak.stdplugins, swak.plugins)
