from __future__ import print_function

import sys

import click

from swak.util import check_python_version
from swak.plugin import enumerate_plugins


check_python_version()


def parse_test_commands(cmd):
    for cmd in cmd.split('|'):
        args = cmd.split()
        assert len(args) > 0
        yield args


def execute_test_cmd(plugins, args):
    pname = args[0]
    pargs = args[1:]
    for pi in plugins:
        if pi.name == pname:
            sys.argv = [pi.name, '--help']
            import pdb; pdb.set_trace()  # XXX BREAKPOINT
            plugin = pi.main()
            pass


@click.group()
def cli():
    pass


@cli.command(help="List installed plugins.")
def list():
    cnt = 1
    print("Swak has {} plugin(s):".format(cnt))
    print("------------------------------------------")
    for pi in enumerate_plugins():
        print("{:13s} - {}".format(pi.name, pi.desc))
    print("------------------------------------------")


@cli.command(help="Show help message for a plugin.")
@click.argument('plugin')
def desc(plugin):
    found = False
    for pi in enumerate_plugins():
        if pi.name == plugin:
            sys.argv = [pi.name, '--help']
            pi.module.main()
            found = True
            break
    if not found:
        print("Can not find plugin '{}'".format(plugin), file=sys.stderr)


@cli.command(help="Run test commands.")
@click.argument('commands')
def run(commands):
    plugins = list(enumerate_plugins())
    for tcmd in parse_test_commands(commands):
        execute_test_cmd(plugins, tcmd)
