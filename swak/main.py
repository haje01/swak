from __future__ import print_function

import sys

import click
from tabulate import tabulate

from swak.util import check_python_version
from swak.plugin import enumerate_plugins, check_plugins_initpy

check_python_version()
check_plugins_initpy(enumerate_plugins())

import swak.plugins


def parse_test_commands(cmd):
    for cmd in cmd.split('|'):
        args = cmd.split()
        assert len(args) > 0
        yield args


def execute_test_cmd(plugins, args):
    pname = args[0]
    for pi in plugins:
        if pi.name == pname:
            pass


@click.group()
def cli():
    pass


@cli.command(help="List installed plugins.")
def list():
    mmap = swak.plugins.MODULE_MAP
    cnt = len(mmap)
    mnames = sorted(mmap.keys())
    plugins = []
    for mname in mnames:
        desc = mmap[mname].main.help
        info = [mname, desc]
        plugins.append(info)

    print("Swak has {} plugin(s):".format(cnt))
    header = ['Plugin', 'Short description']
    print(tabulate(plugins, headers=header, tablefmt='psql'))


@cli.command(help="Show help message for a plugin.")
@click.argument('plugin')
def desc(plugin):
    found = False
    mmap = swak.plugins.MODULE_MAP
    if plugin in mmap:
        sys.argv = [plugin, '--help']
        mmap[plugin].main()
    else:
        print("Can not find plugin '{}'".format(plugin), file=sys.stderr)


@cli.command(help="Run test commands.")
@click.argument('commands')
def run(commands):
    mmap = swak.plugins.MODULE_MAP
    for tcmd in parse_test_commands(commands):
        execute_test_cmd(plugins, tcmd)
