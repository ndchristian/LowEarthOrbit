import click

@click.group()
def cli():
    pass
@cli.command()
def delete():
    click.echo("delete")
@cli.command()
def deploy():
    click.echo("deploy")

@cli.command()
def plan():
    click.echo("plan")

@cli.command()
def validate():
    click.echo("validate")
