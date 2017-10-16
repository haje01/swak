"""This module implements command line interface."""

from __future__ import print_function

import re
import sys
import logging

import click
from tabulate import tabulate

from swak.util import check_python_version, set_log_verbosity
from swak.plugin import PREFIX, get_plugins_dir, init_plugin_dir,\
    iter_plugins
from swak.core import TRunAgent

check_python_version()

PLUGIN_DIR = get_plugins_dir(False)

INIT_PREFIX = ['it', 'ir'] + [p for p in PREFIX[1:]]
ptrn_classnm = re.compile('[A-Z][a-zA-Z0-9_]+')


@click.group()
@click.option('-v', '--verbose', count=True, help="Increase verbosity.")
@click.pass_context
def main(ctx, verbose):
    """Entry for CLI."""
    ctx.obj['verbosity'] = verbose


def validate_init_args(file_name, class_name):
    """Validate file & class name for init command."""
    for pr in PREFIX:
        if file_name.startswith('{}_'.format(pr)):
            logging.error("FILE_NAME should not contain plugin prefix. ({}_)"
                          .format(pr))
            return False
    if ptrn_classnm.match(class_name) is None:
        logging.error("{} is not suitable class name style.")
        return False
    return True


# if not packeged into binary
if not getattr(sys, 'frozen', False):
    # support init command
    @main.command(help='Init new plugin package.')
    @click.option('-t', '--type', "ptypes", type=click.Choice(INIT_PREFIX),
                  default="m", show_default=True, multiple=True,
                  help="Plugin module type prefix.")
    @click.option('-d', '--dir', 'pdir', type=click.Path(exists=True),
                  default=PLUGIN_DIR, show_default=True, help="Plugin "
                  "directory")
    @click.argument('file_name')
    @click.argument('class_name')
    @click.pass_context
    def init(ctx, ptypes, file_name, class_name, pdir):
        """Init new plugin package."""
        if not validate_init_args(file_name, class_name):
            sys.exit(-1)
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

        # check duplicate input types
        if 'it' in ptypes and 'ir' in ptypes:
            logging.error("Text input & Record input plugins are mutually "
                          "exclusive.")
            sys.exit(-1)
        init_plugin_dir(ptypes, file_name, class_name, pdir)


@main.command(help="List known plugins.")
@click.pass_context
def list(ctx):
    """List known plugins."""
    prepare_cli(ctx)

    def list_plugins(standard):
        plugins = []
        pinfos = [(pi.pname, pi.module) for pi in iter_plugins(standard,
                                                               warn=True)]
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
@click.option('-s', '--sub-command', 'subcmd', help="Show help for a "
              "subcommand.")
@click.pass_context
def desc(ctx, plugin, subcmd):
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
            if subcmd is None:
                args = ['--help']
            else:
                args = [subcmd, '--help']
            pi.module.main(args=args)
            return

    print("Can not find plugin '{}'".format(plugin), file=sys.stderr)


@main.command(help="Run '|' seperated test commands.")
@click.argument('commands')
@click.pass_context
def trun(ctx, commands):
    """Test run.

    Args:
        commands (str): Test command concated with '|'
    """
    prepare_cli(ctx)
    agent = TRunAgent()
    agent.run_commands(commands)


def prepare_cli(ctx):
    """Prepare cli command execution.

    - set log level by verbosity
    """
    verbosity = ctx.obj['verbosity']
    set_log_verbosity(verbosity)
