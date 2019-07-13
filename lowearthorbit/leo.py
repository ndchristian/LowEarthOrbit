import ast
import json
import logging
import os

import boto3
import click

from lowearthorbit.delete import delete_stacks
from lowearthorbit.deploy import deploy_templates
from lowearthorbit.plan import plan_deployment
from lowearthorbit.upload import upload_templates
from lowearthorbit.validate import validate_templates

try:
    import configparser
except ImportError:
    # noinspection PyPep8Naming,PyUnresolvedReferences
    import ConfigParser as configparser

config_parser = configparser.RawConfigParser()

logging.basicConfig(level=logging.ERROR)
log = logging.getLogger(__name__)


class Config(object):

    def __init__(self):
        """Creates a decorator so AWS configuration options can be passed"""
        self.session = ''


class JsonParamType(click.ParamType):
    name = 'json'

    def convert(self, value, param, ctx):
        try:
            json.loads(value)
        except ValueError:
            self.fail('%s is not valid JSON' % value, param, ctx)


class LiteralOption(click.Option):

    def type_cast_value(self, ctx, value):
        """Turns JSON input into a data structure Python can work with"""
        if value is not None:
            if 'file://' in value:
                file_path = os.path.expanduser(value.split('file://')[1])
                if os.path.exists(file_path):
                    with open(file_path, 'r') as json_structure:
                        value = json_structure.read()
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError):
            if value is not None:
                raise click.BadParameter(value)


class NotRequiredIf(click.Option):
    """Allows option requirement conditions"""

    def __init__(self, *args, **kwargs):
        self.not_required_if = kwargs.pop('not_required_if')
        assert self.not_required_if, "'not_required_if' parameter required"
        super(NotRequiredIf, self).__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        we_are_present = self.name in opts
        other_present = self.not_required_if in opts

        if not we_are_present:
            if not other_present:
                raise click.UsageError(
                    "You must specify `{}` and/or `{}`".format(
                        self.name,
                        self.not_required_if)
                )
            else:
                self.prompt = None

        return super(NotRequiredIf, self).handle_parse_result(
            ctx, opts, args)


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
@click.option(
    '--botocore-session',
    type=click.STRING,
    help='Use this Botocore session instead of creating a new default one')
@click.option(
    '--profile',
    type=click.STRING,
    help='The name of a profile to use. If not given, then the default profile is used')
@click.option('--region', type=click.STRING,
              help='Region when creating new connections')
@click.option('--debug', is_flag=True,
              help='Shows debug output')
@pass_config
def cli(
        config,
        aws_access_key_id,
        aws_secret_access_key,
        aws_session_token,
        botocore_session,
        profile,
        region,
        debug):
    """Creates the connection to AWS with the specified session arguments"""
    try:
        if debug:
            log.warning("Sensitive details may be in output")
            log.setLevel(logging.DEBUG)

        session_arguments = {}
        session_arguments.update(
            parse_args(
                {
                    'aws_access_key_id': aws_access_key_id,
                    'aws_secret_access_key': aws_secret_access_key,
                    'aws_session_token': aws_session_token,
                    'botocore_session': botocore_session,
                    'profile_name': profile,
                    'region_name': region}))

        log.debug("Boto session arguments : {}".format(session_arguments))
        config.session = boto3.session.Session(**session_arguments)
    except Exception as e:
        log.exception('Error: {}'.format(e))
        exit(1)


@cli.command()
@click.option(
    '--job-identifier',
    type=click.STRING,
    cls=NotRequiredIf,
    not_required_if='config_name',
    help='Prefix that is used to identify stacks to delete')
@click.option('--config-name', type=click.STRING,
              help="Name of the configuration.")
@pass_config
def delete(config, job_identifier, config_name):
    """Deletes all stacks with the given job identifier"""

    delete_arguments = {}
    delete_arguments.update(
        {'session': config.session, 'job_identifier': job_identifier})
    if config_name is not None:
        leo_path = "{}/.leo".format(os.path.expanduser("~"))
        config_parser.read(leo_path)
        try:
            options = config_parser.options(config_name)
            for option in options:
                delete_arguments.update(
                    {option: config_parser.get(config_name, option)})
        except configparser.NoSectionError:
            click.echo('No config called "{}" found'.format(config_name))

        if job_identifier is None and 'job_identifier' not in delete_arguments:
            raise click.ClickException("No job identifier specified")

    delete_arguments.update(parse_args(
        {'session': config.session, 'job_identifier': job_identifier}))

    try:
        log.debug('Delete arguments: {}'.format(delete_arguments))
        exit(delete_stacks(**delete_arguments))
    except Exception as e:
        log.exception('Error: {}'.format(e))
        exit(1)


@cli.command()
@click.option(
    '--bucket',
    type=click.STRING,
    cls=NotRequiredIf,
    not_required_if='config_name',
    help="S3 bucket that has the CloudFormation templates.")
@click.option(
    '--prefix',
    type=click.STRING,
    help='Prefix or bucket subdirectory where CloudFormation templates are located.')
@click.option('--gated', type=click.BOOL,
              help='Checks with user before deploying an update')
@click.option(
    '--job-identifier',
    type=click.STRING,
    cls=NotRequiredIf,
    not_required_if='config_name',
    help='Prefix that is added on to the deployed stack names')
@click.option('--parameters', cls=LiteralOption,
              help='All parameters that are needed to deploy with.')
@click.option(
    '--notification-arns',
    cls=LiteralOption,
    help='All parameters that are needed to deploy with. '
         'Can either be from a JSON file or typed JSON that must be in quotes')
@click.option(
    '--rollback-configuration',
    cls=LiteralOption,
    help='The rollback triggers for AWS CloudFormation to monitor during stack creation '
         'and updating operations, and for the specified monitoring period afterwards.')
@click.option('--tags', cls=LiteralOption,
              help='Tags added to all deployed stacks')
@click.option('--config-name', type=click.STRING,
              help="Name of the configuration.")
@pass_config
def deploy(config, bucket, prefix, gated, job_identifier,
           parameters, notification_arns, rollback_configuration,
           tags, config_name):
    """Creates or updates cloudformation stacks"""
    deploy_arguments = {}

    if config_name is not None:
        leo_path = "{}/.leo".format(os.path.expanduser("~"))
        config_parser.read(leo_path)
        try:
            options = config_parser.options(config_name)
            for option in options:
                try:
                    deploy_arguments.update({option: ast.literal_eval(
                        config_parser.get(config_name, option))})
                except (ValueError, SyntaxError):
                    deploy_arguments.update(
                        {option: config_parser.get(config_name, option)})
        except configparser.NoSectionError:
            click.echo('No config called "{}" found'.format(config_name))

    # Click defaults were overriding config values
    if parameters is None and 'parameters' not in deploy_arguments:
        parameters = []
    if gated is None and 'gated' not in deploy_arguments:
        gated = False
    if job_identifier is None and 'job_identifier' not in deploy_arguments:
        raise click.ClickException("job-identifier does not have a value.")

    deploy_arguments.update(parse_args(
        arguments={'session': config.session, 'bucket': bucket,
                   'prefix': prefix, 'gated': gated,
                   'job_identifier': job_identifier,
                   'parameters': parameters,
                   'notification_arns': notification_arns,
                   'rollback_configuration': rollback_configuration,
                   'Tags': tags}))
    try:
        log.debug('Deploy arguments: {}'.format(deploy_arguments))
        exit(deploy_templates(**deploy_arguments))
    except Exception as e:
        log.exception('Error: {}'.format(e))
        exit(1)


@cli.command()
@click.option('--bucket', type=click.STRING, cls=NotRequiredIf,
              not_required_if='config_name',
              help="S3 bucket that has the CloudFormation templates.")
@click.option(
    '--prefix',
    type=click.STRING,
    help='Prefix or bucket subdirectory where CloudFormation templates are located.')
@click.option('--job-identifier', type=click.STRING, cls=NotRequiredIf,
              not_required_if='config_name',
              help='Prefix that is used to identify stacks')
@click.option(
    '--parameters',
    cls=LiteralOption,
    help='All parameters that are needed to create an accurate plan.')
@click.option('--config-name', type=click.STRING,
              help="Name of the configuration.")
@pass_config
def plan(config, bucket, prefix, job_identifier, parameters, config_name):
    """Attempts to provide information of how an update/creation of stacks might look like and how much it will cost"""
    plan_arguments = {}

    if config_name is not None:
        leo_path = "{}/.leo".format(os.path.expanduser("~"))
        config_parser.read(leo_path)
        try:
            options = config_parser.options(config_name)
            for option in options:
                try:
                    plan_arguments.update({option: ast.literal_eval(
                        config_parser.get(config_name, option))})
                except (ValueError, SyntaxError):
                    plan_arguments.update(
                        {option: config_parser.get(config_name, option)})
        except configparser.NoSectionError:
            click.echo('No config called "{}" found'.format(config_name))

    # Click defaults were overriding config values
    if parameters is None and 'parameters' not in plan_arguments:
        parameters = []
    if job_identifier is None and 'job_identifier' not in plan_arguments:
        raise click.ClickException("job-identifier does not have a value.")

    plan_arguments.update(parse_args(
        arguments={'session': config.session, 'bucket': bucket,
                   'prefix': prefix, 'job_identifier': job_identifier,
                   'parameters': parameters}))
    try:
        log.debug("Plan arguments: {}".format(plan_arguments))
        exit(plan_deployment(**plan_arguments))
    except Exception as e:
        log.exception('Error: {}'.format(e))


@cli.command()
@click.option(
    '--bucket',
    type=click.STRING,
    cls=NotRequiredIf,
    not_required_if='config_name',
    help="S3 bucket that the CloudFormation templates will be uploaded to.")
@click.option(
    '--prefix',
    type=click.STRING,
    help='Prefix or bucket subdirectory where CloudFormation templates will be uploaded to.')
@click.option(
    '--local-path',
    type=click.Path(
        exists=True),
    cls=NotRequiredIf,
    not_required_if='config_name',
    help='Local path where CloudFormation templates are located.')
@click.option('--config-name', type=click.STRING,
              help="Name of the configuration.")
@pass_config
def upload(config, bucket, prefix, local_path, config_name):
    """Uploads all templates to S3"""
    upload_arguments = {}

    if config_name is not None:
        config_parser.read("{}/.leo".format(os.path.expanduser("~")))
        try:
            options = config_parser.options(config_name)
            for option in options:
                upload_arguments.update(
                    {option: config_parser.get(config_name, option)})
        except configparser.NoSectionError:
            click.echo('No config called "{}" found'.format(config_name))

    upload_arguments.update(
        parse_args(
            arguments={
                'session': config.session,
                'bucket': bucket,
                'prefix': prefix,
                'local_path': local_path}))

    # Click defaults were overriding config values
    if bucket is None and 'bucket' not in upload_arguments:
        raise click.ClickException("Bucket does not have a value.")
    if local_path is None and 'local_path' not in upload_arguments:
        raise click.ClickException("local-path does not have a value.")

    try:
        log.debug("Upload arguments: {}".format(upload_arguments))
        exit(upload_templates(**upload_arguments))
    except Exception as e:
        log.exception('Error: {}'.format(e))
        exit(1)


@cli.command()
@click.option(
    '--bucket',
    type=click.STRING,
    cls=NotRequiredIf,
    not_required_if='config_name',
    help="S3 bucket that has the CloudFormation templates.")
@click.option(
    '--prefix',
    type=click.STRING,
    help='Prefix or bucket subdirectory where CloudFormation templates are located.')
@click.option('--config-name', type=click.STRING,
              help="Name of the configuration.")
@pass_config
def validate(config, bucket, prefix, config_name):
    """Validates all templates"""
    validate_arguments = {}

    if config_name is not None:
        config_parser.read("{}/.leo".format(os.path.expanduser("~")))
        try:
            options = config_parser.options(config_name)
            for option in options:
                validate_arguments.update(
                    {option: config_parser.get(config_name, option)})
        except configparser.NoSectionError:
            click.echo('No config called "{}" found'.format(config_name))

    validate_arguments.update(
        parse_args(
            arguments={
                'session': config.session,
                'bucket': bucket,
                'prefix': prefix}))

    if bucket is None and 'bucket' not in validate_arguments:
        raise click.ClickException("Bucket does not have a value.")

    # Displays all validation errors
    try:
        log.debug("Validate arguments: {}".format(validate_arguments))
        validation_errors = exit(validate_templates(**validate_arguments))
        if validation_errors:
            click.echo("Following errors occurred when validating templates:")
            for error in validation_errors:
                click.echo('{}: {}'.format(error['Template'], error['Error']))
    except Exception as e:
        log.exception('Error: {}'.format(e))
        exit(1)


# Config arguments

# noinspection PyUnusedLocal
@cli.command()
@click.option('--config-name', type=click.STRING, required=True,
              help="Name of the configuration.")
@click.option('--bucket', type=click.STRING,
              help="S3 bucket that has the CloudFormation templates.")
@click.option(
    '--prefix',
    type=click.STRING,
    help='Prefix or bucket subdirectory where CloudFormation templates are located.')
@click.option('--gated', type=click.BOOL,
              help='Checks with user before deploying an update')
@click.option('--local-path', type=click.Path(),
              help='Local path where CloudFormation templates are located.')
@click.option('--job-identifier', type=click.STRING,
              help='Prefix that is used to identify stacks')
@click.option(
    '--parameters',
    cls=LiteralOption,
    help='All parameters that are needed to create an accurate plan.')
@click.option(
    '--notification-arns',
    cls=LiteralOption,
    help='All parameters that are needed to deploy with. '
         'Can either be from a JSON file or typed JSON that must be in quotes')
@click.option(
    '--rollback-configuration',
    cls=LiteralOption,
    help='The rollback triggers for AWS CloudFormation to monitor during stack creation '
         'and updating operations, and for the specified monitoring period afterwards.')
@click.option('--tags', cls=LiteralOption,
              help='Tags added to all deployed stacks.')
@pass_config
def create_config(
        config,
        config_name,
        bucket,
        prefix,
        gated,
        local_path,
        job_identifier,
        parameters,
        notification_arns,
        rollback_configuration,
        tags):
    """Creates a configuration"""
    create_config_values = {}

    create_config_values.update(
        parse_args(
            arguments={
                'bucket': bucket,
                'prefix': prefix,
                'gated': gated,
                'local_path': local_path,
                'job_identifier': job_identifier,
                'parameters': parameters,
                'notification_arns': notification_arns,
                'rollback_configuration': rollback_configuration,
                'Tags': tags}))

    leo_path = "{}/.leo".format(os.path.expanduser("~"))
    config_parser.read(leo_path)  # preserves previously written sections
    with open(leo_path, 'w') as config_file:
        config_parser.add_section(config_name)
        for key, value in create_config_values.items():
            if key != 'config_name':
                config_parser.set(config_name, key, str(value))
        config_parser.write(config_file)


# noinspection PyUnusedLocal
@cli.command()
@click.option('--config-name', type=click.STRING, required=True,
              help="Name of the configuration.")
@click.option('--bucket', type=click.STRING,
              help="S3 bucket that has the CloudFormation templates.")
@click.option(
    '--prefix',
    type=click.STRING,
    help='Prefix or bucket subdirectory where CloudFormation templates are located.')
@click.option('--gated', type=click.BOOL,
              help='Checks with user before deploying an update')
@click.option('--local-path', type=click.Path(exists=True),
              help='Local path where CloudFormation templates are located.')
@click.option('--job-identifier', type=click.STRING,
              help='Prefix that is used to identify stacks')
@click.option(
    '--parameters',
    cls=LiteralOption,
    help='All parameters that are needed to create an accurate plan.')
@click.option(
    '--notification-arns',
    cls=LiteralOption,
    help='All parameters that are needed to deploy with. '
         'Can either be from a JSON file or typed JSON that must be in quotes')
@click.option(
    '--rollback-configuration',
    cls=LiteralOption,
    help='The rollback triggers for AWS CloudFormation to monitor during stack creation '
         'and updating operations, and for the specified monitoring period afterwards.')
@click.option('--tags', cls=LiteralOption,
              help='Tags added to all deployed stacks')
@pass_config
def edit_config(
        config,
        config_name,
        bucket,
        prefix,
        gated,
        local_path,
        job_identifier,
        parameters,
        notification_arns,
        rollback_configuration,
        tags):
    """Edits a configuration"""
    edit_config_values = {}

    edit_config_values.update(
        parse_args(
            arguments={
                'bucket': bucket,
                'prefix': prefix,
                'gated': gated,
                'local_path': local_path,
                'job_identifier': job_identifier,
                'parameters': parameters,
                'notification_arns': notification_arns,
                'rollback_configuration': rollback_configuration,
                'Tags': tags}))

    leo_path = "{}/.leo".format(os.path.expanduser("~"))
    config_parser.read(leo_path)  # preserves previously written sections
    with open(leo_path, 'w') as config_file:
        for key, value in edit_config_values.items():
            if key != 'config_name':
                config_parser.set(config_name, key, str(value))
        config_parser.write(config_file)


# noinspection PyUnusedLocal
@cli.command()
@click.option('--config-name', type=click.STRING, required=True,
              help="Name of the configuration.")
@pass_config
def delete_config(config, config_name):
    """Deletes a configuration"""

    config_parser.read("{}/.leo".format(os.path.expanduser("~")))
    if config_name is not None:
        config_parser.remove_section(config_name)
        with open("{}/.leo".format(os.path.expanduser("~")), 'w') as config_file:
            config_parser.write(config_file)
    else:
        raise click.BadParameter(
            param=config_name, message="No config specified")


# noinspection PyUnusedLocal
@cli.command()
@click.option('--config-name', type=click.STRING,
              help="Name of the configuration.")
@pass_config
def list_configs(config, config_name):
    """Lists all configurations or if the config_name is specified, the values of a configuration"""

    config_parser.read("{}/.leo".format(os.path.expanduser("~")))

    sections = config_parser.sections()
    if config_name is None:
        if sections:
            for section in sections:
                click.echo(section)
        else:
            click.echo("No configs found")
    else:
        try:
            options = config_parser.options(config_name)
            click.echo("[{}]\n".format(config_name))
            for option in options:
                click.echo("{} = {}".format(
                    option, config_parser.get(config_name, option)))
        except configparser.NoSectionError:
            click.echo('No config called "{}" found'.format(config_name))
