import logging
import time

import botocore
import click

from lowearthorbit.resources.capabilities import get as get_capabilities
from lowearthorbit.resources.changes import display_changes, apply_changes, change_set_delete_waiter
from lowearthorbit.resources.parameters import gather as gather_parameters

log = logging.getLogger(__name__)


def update_stack(**kwargs):
    """Updates stack if there is a stack by the same name"""

    session = kwargs['session']
    key_object = kwargs['key_object']
    stack_name = kwargs['update_stack_name']
    bucket = kwargs['bucket']
    job_identifier = kwargs['job_identifier']
    parameters = kwargs['parameters']
    gated = kwargs['gated']
    deploy_parameters = kwargs['deploy_parameters']

    cfn_client = session.client('cloudformation')
    s3_client = session.client('s3')

    template_url = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket,
                                                            'Key': key_object},
                                                    ExpiresIn=60)

    click.echo("\nCreating change set for {}...".format(stack_name))

    change_set_name = 'change set-{}-{}'.format(stack_name, int(time.time()))
    stack_capabilities = get_capabilities(template_url=template_url, session=session)
    stack_parameters = gather_parameters(session=session,
                                         key_object=key_object, parameters=parameters, bucket=bucket,
                                         job_identifier=job_identifier)

    try:
        change_set = cfn_client.create_change_set(
            StackName=stack_name,
            TemplateURL=template_url,
            Parameters=stack_parameters,
            Capabilities=stack_capabilities,
            ChangeSetName=change_set_name,
            Description="Change set for {} created by Leo".format(stack_name),
            **deploy_parameters
        )
    except botocore.exceptions.ClientError as ChangeSetCreationError:
        raise ChangeSetCreationError

    try:
        cfn_client.get_waiter('change_set_create_complete').wait(ChangeSetName=change_set['Id'])
    except botocore.exceptions.WaiterError as change_set_creation_error:
        long_string_err = "The submitted information didn't contain changes. " \
                          "Submit different information to create a change set."

        if str(cfn_client.describe_change_set(ChangeSetName=change_set['Id'])['StatusReason']) in \
                (long_string_err, "No updates are to be performed."):
            click.echo(cfn_client.describe_change_set(ChangeSetName=change_set['Id'])['StatusReason'])
            pass
        else:
            raise change_set_creation_error

    # Checks for the changes
    change_set_details = cfn_client.describe_change_set(ChangeSetName=change_set['Id'])
    change_set_changes = change_set_details['Changes']

    if change_set_changes:
        display_changes(changes=change_set_changes, name=change_set_name, change_set=True)
        # Acts as a filter on past resource failures
        past_failures = [stack_event for stack_event in
                         cfn_client.describe_stack_events(StackName=stack_name)['StackEvents'] if
                         stack_event['ResourceStatus'] in ['CREATE_FAILED', 'UPDATE_FAILED']]

        if not gated:
            apply_changes(change_set_name=change_set['Id'], change_set=change_set, cfn_client=cfn_client,
                          update_stack_name=stack_name, past_failures=past_failures)
            return {'StackName': stack_name}
        else:
            update_choice = click.confirm("Would you like to execute these changes?")
            if update_choice:
                apply_changes(change_set_name=change_set['Id'], change_set=change_set, cfn_client=cfn_client,
                              update_stack_name=stack_name, past_failures=past_failures)

                return {'StackName': stack_name}

            else:
                click.echo("Moving on from executing {}".format(change_set_name))
                click.echo("Deleting change set {}...".format(change_set_name))
                cfn_client.delete_change_set(ChangeSetName=change_set['Id'],
                                             StackName=stack_name)
                # Check if still needed
                change_set_delete_waiter(change_set_id=change_set['Id'], cfn_client=cfn_client)

    else:
        # If there are no changes it passes and deletes the change set
        click.echo("No changes found for {}".format(stack_name))
        click.echo("Deleting change set for {}...".format(change_set_name))
        cfn_client.delete_change_set(ChangeSetName=change_set['Id'], StackName=stack_name)
        change_set_delete_waiter(change_set_id=change_set['Id'], cfn_client=cfn_client)
