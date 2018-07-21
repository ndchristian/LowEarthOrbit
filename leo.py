import boto3
import click

from lowearthorbit.validate import validate_templates


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
@click.option('--bucket', type=click.STRING, required=True,
              help="S3 bucket that has the CloudFormation templates.")
@click.option('--prefix', type=click.STRING, default='',
              help='Prefix or bucket subdirectory where CloudFormation templates are located.')
@pass_config
def validate(config, bucket, prefix):
    validation_errors = validate_templates(session=config.session,
                                           bucket=bucket,
                                           prefix=prefix)

    if validation_errors:
        click.echo("Following errors occured when validating templates:")
        for error in validation_errors:
            click.echo(error)
