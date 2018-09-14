import boto3
import click

from lowearthorbit.delete import delete_stacks
from lowearthorbit.deploy import deploy_templates
from lowearthorbit.upload import upload_templates
from lowearthorbit.validate import validate_templates


class Config(object):
    def __init__(self):
        self.session = ''


pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option('--aws-access-key-id', type=click.STRING, default=None,
              help='AWS access key ID')
@click.option('--aws-secret-access-key', type=click.STRING, default=None,
              help='AWS secret access key')
@click.option('--aws_session_token', type=click.STRING, default=None,
              help='AWS temporary session token')
@click.option('--botocore-session', type=click.STRING, default=None,
              help='Use this Botocore session instead of creating a new default one')
@click.option('--profile', type=click.STRING, default=None,
              help='The name of a profile to use. If not given, then the default profile is used')
@click.option('--region', type=click.STRING, default=None,
              help='Region when creating new connections')
@pass_config
def cli(config, aws_access_key_id, aws_secret_access_key_id, aws_session_token, botocore_session, profile, region):
    session_arguments = {}
    if aws_access_key_id is not None:
        session_arguments.update({'aws_access_key_id': aws_access_key_id})
    if aws_secret_access_key_id is not None:
        session_arguments.update({'aws_secret_access_key_id': aws_secret_access_key_id})
    if aws_session_token is not None:
        session_arguments.update({'aws_session_token': aws_session_token})
    if botocore_session is not None:
        session_arguments.update({'botocore_session': botocore_session})
    if profile is not None:
        session_arguments.update({'profile_name': profile})
    if region is not None:
        session_arguments.update({'region_name': region})

    config.session = boto3.session.Session(**session_arguments)


@cli.command()
@click.option('--job-identifier', type=click.STRING, required=True,
              help='Prefix that is used to identify stacks to delete')
@pass_config
def delete(config, job_identifier):
    delete_stacks(session=config.session, job_identifier=job_identifier)


@cli.command()
@click.option('--bucket', type=click.STRING, required=True,
              help="S3 bucket that has the CloudFormation templates.")
@click.option('--prefix', type=click.STRING, default='',
              help='Prefix or bucket subdirectory where CloudFormation templates are located.')
@click.option('--gated', type=click.BOOL, default=False,
              help='Checks with user before deploying an update')
@click.option('--job-identifier', type=click.STRING, required=True,
              help='Prefix that is added on to the deployed stack names')
@click.option('--parameters', type=click.STRING, default=[],
              help='All parameters that are needed to deploy with. '
                   'Can either be from a JSON file or typed JSON that must be in quotes')
@click.option('--tags', type=click.STRING, default=[],
              help='Tags added to all deployed stacks')
@pass_config
def deploy(config, bucket, prefix, gated, job_identifier, parameters, tags):
    deploy_templates(session=config.session,
                     bucket=bucket,
                     gated=gated,
                     job_identifier=job_identifier,
                     parameters=parameters,
                     prefix=prefix,
                     tags=tags)


@cli.command()
def plan():
    click.echo("plan")


@cli.command()
@click.option('--bucket', type=click.STRING, required=True,
              help="S3 bucket that the CloudFormation templates will be uploaded to.")
@click.option('--prefix', type=click.STRING, default='',
              help='Prefix or bucket subdirectory where CloudFormation templates will be uploaded to.')
@click.option('--localpath', type=click.Path(exists=True), required=True,
              help='Local path where CloudFormation templates are located.')
@pass_config
def upload(config, bucket, prefix, localpath):
    upload_templates(Bucket=bucket,
                     Prefix=prefix,
                     Session=config.session,
                     LocalPath=localpath)


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
