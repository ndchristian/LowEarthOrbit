import json
import sys
import time
import botocore
import click

from lowearthorbit.resources.capabilities import get as get_capabilities
from lowearthorbit.resources.changes import display_changes, change_set_delete_waiter
from lowearthorbit.resources.parameters import gather as gather_parameters

STACK_LIST = []


def get_stack_name(job_identifier, obj):
    """Formats the stack name and make sure it meets LEO and CloudFormations naming requirements."""

    stack_name = "{}-{}".format(job_identifier, obj)
    # Below checks if the stack_name meets all requirements.
    stack_name_parts = []
    if not stack_name[0].isalpha():
        stack_name = "s-" + stack_name
    if len(stack_name) > 255:
        stack_name = stack_name[:255]
    for s in stack_name:
        if not s.isalnum():
            s = s.replace(s, "-")
            stack_name_parts.append(s)
        else:
            stack_name_parts.append(s)
    stack_name = "".join(stack_name_parts)

    return stack_name


def transform_template(
        cfn_client,
        stack_name,
        template_url,
        stack_parameters,
        deploy_parameters):
    """Handles templates that transform, such as templates that are using SAM."""

    # Gathering capabilities is a bit wacky with templates that transform
    click.echo("Gathering information needed to transform the template")
    try:
        change_set_name = 'changeset-{}-{}'.format(
            stack_name, int(time.time()))
        transform_stack_details = cfn_client.create_change_set(
            StackName=stack_name,
            TemplateURL=template_url,
            Parameters=stack_parameters,
            Capabilities=['CAPABILITY_IAM',
                          'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND'],
            ChangeSetName=change_set_name,
            Description="Transformation details change set for {} created by Leo".format(
                stack_name),
            ChangeSetType='CREATE',
            **deploy_parameters
        )

        cfn_client.get_waiter('change_set_create_complete').wait(
            ChangeSetName=transform_stack_details['Id']
        )
    except botocore.exceptions.WaiterError:
        change_set_failed_reason = cfn_client.describe_change_set(
            ChangeSetName=transform_stack_details['Id'])['StatusReason']

        raise change_set_failed_reason

    new_template = cfn_client.get_template(
        ChangeSetName=transform_stack_details['Id'],
        TemplateStage="Processed"
    )

    new_template_capabilities = cfn_client.get_template_summary(
        TemplateBody=json.dumps(
            new_template['TemplateBody'], indent=4, default=str)
    )

    cfn_client.delete_change_set(
        ChangeSetName=transform_stack_details['Id']
    )

    click.echo("Transforming template")

    if 'Capabilities' in new_template_capabilities:
        iam_capabilities = new_template_capabilities['Capabilities']
    else:
        iam_capabilities = []

    transform_stack = cfn_client.create_change_set(
        StackName=stack_name,
        TemplateURL=template_url,
        Parameters=stack_parameters,
        Capabilities=iam_capabilities,
        ChangeSetName='changeset-{}-{}'.format(stack_name, int(time.time())),
        Description="Transformation change set for {} created by Leo".format(
            stack_name),
        ChangeSetType='CREATE',
        **deploy_parameters
    )

    cfn_client.get_waiter('change_set_create_complete').wait(
        ChangeSetName=transform_stack['Id']
    )

    return transform_stack


def display_status(cfn_client, current_stack, stack_name):
    """Tells the user what's going on when the stack is being created"""

    STACK_LIST.append(
        {'StackId': current_stack['StackId'], 'StackName': stack_name})
    stack_description = cfn_client.describe_stacks(
        StackName=current_stack['StackId'])['Stacks'][0]['Description']
    click.echo("Description: \n\t{}".format(stack_description))
    click.echo("\nCreating...")
    try:
        cfn_client.get_waiter('stack_create_complete').wait(
            StackName=current_stack['StackId'])
        click.echo("Created {}.".format(stack_name))

        return {'StackName': stack_name}
    except botocore.exceptions.WaiterError:
        click.echo("\n{} is currently rolling back.".format(stack_name))
        resource_failures = [{'LogicalResourceId': event['LogicalResourceId'],
                              'ResourceStatusReason': event['ResourceStatusReason']} for event in
                             cfn_client.describe_stack_events(
                                 StackName=current_stack['StackId'])['StackEvents']
                             if event['ResourceStatus'] == 'CREATE_FAILED']

        if resource_failures:
            for failures in resource_failures:
                click.echo(
                    "%s has failed to be created because: '%s'" %
                    (failures['LogicalResourceId'],
                     failures['ResourceStatusReason']))
        else:
            click.echo(
                "Please check console for why some resources failed to create.")

        sys.exit()


def create_stack(**kwargs):
    """Creates the stack and handles rollback conditions"""

    session = kwargs['session']
    key_object = kwargs['key_object']
    bucket = kwargs['bucket']
    job_identifier = kwargs['job_identifier']
    gated = kwargs['gated']
    parameters = kwargs['parameters']
    deploy_parameters = kwargs['deploy_parameters']

    cfn_client = session.client('cloudformation')
    s3_client = session.client('s3')

    template_url = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket,
                                                            'Key': key_object},
                                                    ExpiresIn=60)
    template_summary = cfn_client.get_template_summary(
        TemplateURL=template_url)

    stack_name = get_stack_name(job_identifier=job_identifier, obj=str(
        key_object).split("/")[-1].split(".")[0])
    click.echo("\n{}:".format(stack_name))

    stack_capabilities = get_capabilities(
        template_url=template_url, session=session)

    stack_parameters = gather_parameters(
        session=session,
        key_object=key_object,
        parameters=parameters,
        bucket=bucket)

    try:
        # Templates with declared transformations need to be transformed before
        # being fed to CloudFormation
        transformed = False
        if 'DeclaredTransforms' in template_summary:
            transformed_stack = transform_template(
                cfn_client=cfn_client,
                stack_name=stack_name,
                template_url=template_url,
                stack_parameters=stack_parameters,
                deploy_parameters=deploy_parameters)

            # Checks for the changes
            change_set_details = cfn_client.describe_change_set(
                ChangeSetName=transformed_stack['Id'])
            change_set_changes = change_set_details['Changes']
            display_changes(changes=change_set_changes, change_set=True)
            transformed = True

        else:
            try:
                cost_url = cfn_client.estimate_template_cost(
                    TemplateURL=template_url, Parameters=stack_parameters)['Url']
            except (botocore.exceptions.ClientError, botocore.exceptions.ParamValidationError):
                cost_url = None

            click.echo("Estimated template cost URL: {}".format(cost_url))
            display_changes(
                changes=template_summary['ResourceTypes'], change_set=False)

        if gated:
            execute_changes = click.confirm("\nWould you like to deploy?")
            if execute_changes:
                if transformed:
                    cfn_client.execute_change_set(
                        ChangeSetName=transformed_stack['Id'], StackName=stack_name)
                    current_stack = cfn_client.describe_stacks(
                        StackName=stack_name)['Stacks'][0]
                else:
                    current_stack = cfn_client.create_stack(
                        StackName=stack_name,
                        TemplateURL=template_url,
                        Parameters=stack_parameters,
                        Capabilities=stack_capabilities,
                        DisableRollback=False,
                        TimeoutInMinutes=123,
                        **deploy_parameters)

                display_status(
                    cfn_client=cfn_client,
                    current_stack=current_stack,
                    stack_name=stack_name)

                return {'StackName': stack_name}

            else:
                if transformed:
                    click.echo("Deleting change set {}...".format(
                        transformed_stack['Id']))
                    cfn_client.delete_change_set(
                        ChangeSetName=transformed_stack['Id'], StackName=stack_name)
                    # Check if still needed
                    change_set_delete_waiter(
                        change_set_id=transformed_stack['Id'],
                        cfn_client=cfn_client)

        else:
            if transformed:
                cfn_client.execute_change_set(
                    ChangeSetName=transformed_stack['Id'],
                    StackName=stack_name)
                current_stack = cfn_client.describe_stacks(
                    StackName=stack_name)['Stacks'][0]
            else:
                current_stack = cfn_client.create_stack(
                    StackName=stack_name,
                    TemplateURL=template_url,
                    Parameters=stack_parameters,
                    Capabilities=stack_capabilities,
                    DisableRollback=False,
                    TimeoutInMinutes=123,
                    **deploy_parameters)

            display_status(cfn_client=cfn_client,
                           current_stack=current_stack, stack_name=stack_name)

            return {'StackName': stack_name}

    except botocore.exceptions.ClientError as e:
        raise e
