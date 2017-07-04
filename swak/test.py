import os

import click


@click.command()
@click.option('--home', type=click.Path(exists=True), help="Home directory.")
@click.option('--task', type=int, default=1, show_default=True, help="Task"
              " number to test.")
@click.option('--version', is_flag=True, help="Show Swak version.")
def run(home, task, version):
    _run(home, task, version)


def _run(home, task, version):
    if version:
        path = os.path.join(os.path.dirname(__file__), 'version.txt')
        with open(path, 'rt') as f:
            VERSION = f.read().strip()
        print("Swak version {}".format(VERSION))
        return

    print(home)
    print(task)


if __name__ == '__main__':
    run()
