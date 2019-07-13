import time

import botocore
import click

from lowearthorbit.deploy import deploy_type
from lowearthorbit.resources.capabilities import get as get_capabilities
from lowearthorbit.resources.changes import display_changes
from lowearthorbit.resources.parameters import gather


def create_plan(
        session,
        bucket,
        s3_object_key,
        job_identifier,
        parameters,
        template_url):
    """Shows a plan of what CloudFormation might create and how much it might cost"""

    cfn_client = session.client('cloudformation')

    template_summary = cfn_client.get_template_summary(
        TemplateURL=template_url)
    stack_parameters = gather(
        session=session,
        key_object=s3_object_key,
        parameters=parameters,
        bucket=bucket,
        job_identifier=job_identifier)
    try:
        cost_url = cfn_client.estimate_template_cost(
            TemplateURL=template_url, Parameters=stack_parameters)['Url']
    except (botocore.exceptions.ClientError, botocore.exceptions.ParamValidationError):
        cost_url = None

    click.echo("Estimated template cost URL: {}".format(cost_url))
    display_changes(
        changes=template_summary['ResourceTypes'], change_set=False)


def update_plan(
        session,
        stack_name,
        s3_object_key,
        template_url,
        job_identifier,
        parameters,
        bucket):
    """Shows a plan of what CloudFormation might update and how much it might cost"""

    cfn_client = session.client('cloudformation')

    click.echo("\nCreating change set for {}...".format(stack_name))

    change_set_name = 'changeset-{}-{}'.format(stack_name, int(time.time()))
    stack_capabilities = get_capabilities(
        template_url=template_url, session=session)

    stack_parameters = gather(session=session,
                              key_object=s3_object_key,
                              parameters=parameters,
                              bucket=bucket,
                              job_identifier=job_identifier)

    try:
        change_set = cfn_client.create_change_set(
            StackName=stack_name,
            TemplateURL=template_url,
            Parameters=stack_parameters,
            Capabilities=stack_capabilities,
            ChangeSetName=change_set_name,
            Description="Change set for {} created by Leo".format(stack_name),
        )
    except botocore.exceptions.ClientError as ChangeSetCreationError:
        raise ChangeSetCreationError

    try:
        cfn_client.get_waiter('change_set_create_complete').wait(
            ChangeSetName=change_set['Id'])
    except botocore.exceptions.WaiterError as change_set_creation_error:
        long_string_err = "The submitted information didn't contain changes. " \
                          "Submit different information to create a change set."

        if str(
                cfn_client.describe_change_set(
                    ChangeSetName=change_set['Id'])['StatusReason']) in (
                long_string_err,
                "No updates are to be performed."):
            click.echo(cfn_client.describe_change_set(
                ChangeSetName=change_set['Id'])['StatusReason'])
            pass
        else:
            raise change_set_creation_error

    # Checks for the changes
    change_set_details = cfn_client.describe_change_set(
        ChangeSetName=change_set['Id'])
    change_set_changes = change_set_details['Changes']

    try:
        cost_url = cfn_client.estimate_template_cost(
            TemplateURL=template_url, Parameters=stack_parameters)['Url']
    except (botocore.exceptions.ClientError, botocore.exceptions.ParamValidationError):
        cost_url = None
    click.echo("Cost estimate for these resources : {}".format(cost_url))
    if change_set_changes:
        display_changes(changes=change_set_changes, change_set=True)
    else:
        click.echo("No changes to be found")


def plan_deployment(**kwargs):
    """Displays what CloudFormation might create/update and what it might cost """

    cfn_ext = ('.json', '.template', '.txt', 'yaml', 'yml')

    session = kwargs['session']
    bucket = kwargs['bucket']
    job_identifier = kwargs['job_identifier']
    parameters = kwargs['parameters']

    objects_parameters = {}
    objects_parameters.update({'Bucket': bucket})
    if 'prefix' in kwargs:
        objects_parameters.update({'Prefix': kwargs['prefix']})

    s3_client = session.client('s3')
    cfn_client = session.client('cloudformation')

    stack_counter = 0
    for s3_object in s3_client.list_objects_v2(
            **objects_parameters)['Contents']:
        if s3_object['Key'].endswith(cfn_ext) and s3_object['Key'].split(
                '/')[-1].startswith('{:02d}'.format(stack_counter)):
            # Only lets through S3 objects with the names properly formatted
            # for LEO
            stack_name = "{}-{}".format(job_identifier,
                                        str(s3_object['Key'].split('/')[-1]).rsplit('.',
                                                                                    1)[0])

            template_url = s3_client.generate_presigned_url('get_object',
                                                            Params={'Bucket': bucket,
                                                                    'Key': s3_object['Key']},
                                                            ExpiresIn=60)
            check = deploy_type(stack_name=stack_name,
                                cfn_client=cfn_client)
            if check['Update']:
                update_plan(session=session,
                            stack_name=stack_name,
                            s3_object_key=s3_object['Key'],
                            template_url=template_url,
                            job_identifier=job_identifier,
                            parameters=parameters,
                            bucket=bucket)

            else:  # New stack
                create_plan(session=session,
                            bucket=bucket,
                            s3_object_key=s3_object['Key'],
                            job_identifier=job_identifier,
                            parameters=parameters,
                            template_url=template_url)

            # Allows LEO to progress in the assigned order
            stack_counter += 1
