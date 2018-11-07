import ast
import logging

import boto3
import click

from lowearthorbit.delete import delete_stacks
from lowearthorbit.deploy import deploy_templates
from lowearthorbit.plan import plan_deployment
from lowearthorbit.upload import upload_templates
from lowearthorbit.validate import validate_templates

logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(__name__)


class Config(object):
    def __init__(self):
        """Creates a decorator so AWS configuration options can be passed"""
        self.session = ''


class LiteralOption(click.Option):
    def type_cast_value(self, ctx, value):
        """Turns JSON input into a data structure Python can work with"""
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            if value is not None:
                raise click.BadParameter(value)


def parse_args(arguments):
    """Filters through the options and arguments and only passes those that have a value"""
    argument_parameters = {}
    for key, value in arguments.items():
        if value is not None:
            argument_parameters.update({key: value})

    log.debug("Arguments after parse_args filter: {}".format(argument_parameters))

    return argument_parameters


pass_config = click.make_pass_decorator(Config, ensure=True)


@click.group()
@click.option('--aws-access-key-id', type=click.STRING,
              help='AWS access key ID')
@click.option('--aws-secret-access-key', type=click.STRING,
              help='AWS secret access key')
@click.option('--aws_session_token', type=click.STRING,
              help='AWS temporary session token')
@click.option('--botocore-session', type=click.STRING,
              help='Use this Botocore session instead of creating a new default one')
@click.option('--profile', type=click.STRING,
              help='The name of a profile to use. If not given, then the default profile is used')
@click.option('--region', type=click.STRING,
              help='Region when creating new connections')
@click.option('--debug', is_flag=True,
              help='Shows debug output')
@pass_config
def cli(config, aws_access_key_id, aws_secret_access_key, aws_session_token, botocore_session, profile, region, debug):
    """Creates the connection to AWS with the specified session arguments"""
    try:
        if debug:
            log.warning("Sensitive details may be in output")
            log.setLevel(logging.DEBUG)

        session_arguments = parse_args(arguments=locals())

        # Not boto3 session arguments
        del session_arguments['debug']
        del session_arguments['config']

        log.debug("Boto session arguments : {}".format(session_arguments))
        config.session = boto3.session.Session(**session_arguments)
    except Exception as e:
        log.exception('Error: %s', e)
        exit(1)


@cli.command()
@click.option('--job-identifier', type=click.STRING, required=True,
              help='Prefix that is used to identify stacks to delete')
@pass_config
def delete(config, job_identifier):
    """Deletes all stacks with the given job identifier"""

    delete_arguments = locals()

    # config.session, not config should be passed
    del delete_arguments['config']
    delete_arguments.update({'session': config.session})
    try:
        log.debug('Delete arguments: {}'.format(delete_arguments))
        exit(delete_stacks(**delete_arguments))
    except Exception as e:
        log.exception('Error: %s', e)
        exit(1)


@cli.command()
@click.option('--bucket', type=click.STRING, required=True,
              help="S3 bucket that has the CloudFormation templates.")
@click.option('--prefix', type=click.STRING,
              help='Prefix or bucket subdirectory where CloudFormation templates are located.')
@click.option('--gated', type=click.BOOL, default=False,
              help='Checks with user before deploying an update')
@click.option('--job-identifier', type=click.STRING, required=True,
              help='Prefix that is added on to the deployed stack names')
@click.option('--parameters', cls=LiteralOption, default=[],
              help='All parameters that are needed to deploy with.')
@click.option('--notification-arns', cls=LiteralOption,
              help='All parameters that are needed to deploy with. '
                   'Can either be from a JSON file or typed JSON that must be in quotes')
@click.option('--rollback-configuration', cls=LiteralOption,
              help='The rollback triggers for AWS CloudFormation to monitor during stack creation '
                   'and updating operations, and for the specified monitoring period afterwards.')
@click.option('--tags', cls=LiteralOption,
              help='Tags added to all deployed stacks')
@pass_config
def deploy(config, bucket, prefix, gated, job_identifier, parameters, notification_arns, rollback_configuration, tags):
    """Creates or updates cloudformation stacks"""

    deploy_arguments = parse_args(arguments=locals())

    # config.session, not config should be passed
    del deploy_arguments['config']
    deploy_arguments.update({'session': config.session})

    try:
        log.debug('Deploy arguments: {}'.format(deploy_arguments))
        exit(deploy_templates(**deploy_arguments))
    except Exception as e:
        log.exception('Error: %s', e)
        exit(1)


@cli.command()
@click.option('--bucket', type=click.STRING, required=True,
              help="S3 bucket that has the CloudFormation templates.")
@click.option('--prefix', type=click.STRING,
              help='Prefix or bucket subdirectory where CloudFormation templates are located.')
@click.option('--job-identifier', type=click.STRING, required=True,
              help='Prefix that is used to identify stacks')
@click.option('--parameters', cls=LiteralOption, default=[],
              help='All parameters that are needed to create an accurate plan.')
@pass_config
def plan(config, bucket, prefix, job_identifier, parameters):
    """Attempts to provide information of how an update/creation of stacks might look like and how much it will cost"""

    plan_arguments = parse_args(arguments=locals())

    # config.session, not config should be passed
    del plan_arguments['config']
    plan_arguments.update({'session': config.session})

    try:
        log.debug("Plan arguments: {}".format(plan_arguments))
        exit(plan_deployment(**plan_arguments))
    except Exception as e:
        log.exception('Error: %s', e)
        exit(1)


@cli.command()
@click.option('--bucket', type=click.STRING, required=True,
              help="S3 bucket that the CloudFormation templates will be uploaded to.")
@click.option('--prefix', type=click.STRING,
              help='Prefix or bucket subdirectory where CloudFormation templates will be uploaded to.')
@click.option('--local-path', type=click.Path(exists=True), required=True,
              help='Local path where CloudFormation templates are located.')
@pass_config
def upload(config, bucket, prefix, local_path):
    """Uploads all templates to S3"""

    upload_arguments = parse_args(arguments=locals())

    # config.session, not config should be passed
    del upload_arguments['config']
    upload_arguments.update({'session': config.session})

    try:
        log.debug("Upload arguments: {}".format(upload_arguments))
        exit(upload_templates(**upload_arguments))
    except Exception as e:
        log.exception('Error: %s', e)
        exit(1)


@cli.command()
@click.option('--bucket', type=click.STRING, required=True,
              help="S3 bucket that has the CloudFormation templates.")
@click.option('--prefix', type=click.STRING,
              help='Prefix or bucket subdirectory where CloudFormation templates are located.')
@pass_config
def validate(config, bucket, prefix):
    """Validates all templates"""
    validate_arguments = parse_args(arguments=locals())

    # config.session, not config should be passed
    del validate_arguments['config']
    validate_arguments.update({'session': config.session})

    # Displays all validation errors
    try:
        log.debug("Validate arguments: {}".format(validate_arguments))
        validation_errors = exit(validate_templates(**validate_arguments))
        if validation_errors:
            click.echo("Following errors occurred when validating templates:")
            for error in validation_errors:
                click.echo('%s: %s' % (error['Template'], error['Error']))
    except Exception as e:
        log.exception('Error: %s', e)
        exit(1)
