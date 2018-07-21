import boto3
import click


class Config(object):
    def __init__(self):
        self.session = ''


pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option('--profile', default=None,
              help='Profile in your credentials file to be used to communicate with AWS.')
@click.option('--region', default=None,
              help='Which AWS region to execute in.')
@pass_config
def cli(config, profile, region):
    session_arguments = {}
    if profile is not None:
        session_arguments.update({'profile_name': profile})
    if region is not None:
        session_arguments.update({'region_name': region})

    config.session = boto3.session.Session(**session_arguments)


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
def upload():
    click.echo("upload")


@cli.command()
def validate():
    click.echo("validate")
