import botocore
import click


def delete_stacks(**kwargs):
    """Deletes all stacks with the specified job-identifier"""

    session = kwargs['session']
    job_identifier = kwargs['job_identifier']

    cfn_client = session.client('cloudformation')

    stack_names = sorted([stack['StackName'] for stack in cfn_client.describe_stacks()[
        'Stacks'] if "{}-".format(job_identifier) in stack['StackName']])

    choice = click.confirm(
        "Do you want to delete these stacks? : {}".format(stack_names))
    if choice:
        for stack_name in reversed(stack_names):
            cfn_client.delete_stack(StackName=stack_name)
            try:
                cfn_client.get_waiter('stack_delete_complete').wait(
                    StackName=stack_name)
                click.echo("Deleted {}.".format(stack_name))
            except botocore.exceptions.WaiterError as waiter_error:
                click.echo("{} failed to delete. {}".format(
                    stack_name, waiter_error))
                click.echo("Stopped stack deletion.")
                break
