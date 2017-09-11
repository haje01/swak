"""This module implements command line interface."""

from __future__ import print_function

import sys
import logging

import click
from tabulate import tabulate

from swak.util import check_python_version, set_log_verbosity
from swak.plugin import PREFIX, get_plugins_dir, init_plugin_dir,\
    iter_plugins
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
    # support init command
    @main.command(help='Init new plugin package.')
    @click.option('-t', '--type', "ptypes", type=click.Choice(INIT_PREFIX),
                  default="mod", show_default=True, multiple=True,
                  help="Plugin module type prefix.")
    @click.option('-d', '--dir', 'pdir', type=click.Path(exists=True),
                  default=PLUGIN_DIR, show_default=True, help="Plugin "
                  "directory")
    @click.argument('file_name')
    @click.argument('class_name')
    @click.pass_context
    def init(ctx, ptypes, file_name, class_name, pdir):
        """Init new plugin package."""
        prepare_cli(ctx)

        # check duplicate plugin
        for i in range(2):
            pnames = set([pi.pname for pi in iter_plugins(i == 0)])
            for ptype in ptypes:
                pfname = '{}.{}'.format(ptype, file_name)
                if pfname in pnames:
                    ptypen = 'standard' if i == 0 else 'external'
                    logging.error("Plugin '{}' already exists as {} plugin".
                                  format(pfname, ptypen))
                    sys.exit(-1)

        init_plugin_dir(ptypes, file_name, class_name, pdir)


@main.command(help="List known plugins.")
@click.pass_context
def list(ctx):
    """List known plugins."""
    prepare_cli(ctx)

    def list_plugins(standard):
        plugins = []
        pinfos = [(pi.pname, pi.module) for pi in iter_plugins(standard)]
        pinfos = sorted(pinfos)
        cnt = len(pinfos)
        for pname, pmod in pinfos:
            desc = pmod.main.help
            info = [pname, desc]
            plugins.append(info)

        if standard:
            print("Swak has {} standard plugins:".format(cnt))
        else:
            print("And {} external plugin(s):".format(cnt))

        header = ['Plugin', 'Description']
        print(tabulate(plugins, headers=header, tablefmt='psql'))

    list_plugins(True)
    list_plugins(False)


@main.command(help="Show help message for a plugin.")
@click.argument('plugin')
@click.pass_context
def desc(ctx, plugin):
    """Show help message for a plugin.

    Args:
        plugin (str): Plugin name with prefix
    """
    prepare_cli(ctx)

    for i in range(2):  # standard / external plugins
        for pi in iter_plugins(i == 0):
            if pi.pname != plugin:
                continue
            sys.argv[0] = plugin
            pi.module.main(args=['--help'])
            return

    print("Can not find plugin '{}'".format(plugin), file=sys.stderr)


@main.command(help="Run '|' seperated test commands.")
@click.argument('commands')
@click.pass_context
def test(ctx, commands):
    """Run test commands.

    Args:
        commands (str): Test commands concated with '|'
    """
    prepare_cli(ctx)
    cmds = parse_and_validate_test_cmds(commands)
    run_test_cmds(cmds)


def prepare_cli(ctx):
    """Prepare cli command execution.

    - set log level by verbosity
    """
    verbosity = ctx.obj['verbosity']
    set_log_verbosity(verbosity)
