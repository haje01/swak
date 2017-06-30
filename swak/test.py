import click


@click.command()
@click.option('--home', type=click.Path(exists=True), help="Home directory.")
@click.option('--task', type=int, help="Task number to test.")
def run(home, task):
    print(home)


if __name__ == '__main__':
    run()
