import sys
import time

import botocore
import click


def stack_continue_rollback_waiter(stack_name, cfn_client):
    """Boto3 does not have a waiter for creating rolling back a stack completely, this is a custom one"""

    stack_continue_rollback_counter = 0
    stack_continue_rollback = True

    while stack_continue_rollback:
        stack_details = cfn_client.describe_stacks(
            StackName=stack_name)['Stacks'][0]
        if stack_details['StackStatus'] in 'UPDATE_ROLLBACK_COMPLETE':
            stack_continue_rollback = False

        elif stack_details['StackStatus'] in 'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS':
            if stack_continue_rollback_counter == 120:
                click.echo("\n{}".format(stack_details['StatusReason']))
                sys.exit(
                    "Something went wrong while trying to rollback the stack. Please check the console.")
            else:
                stack_continue_rollback_counter += 1
                time.sleep(15)

        elif stack_details['StackStatus'] in 'UPDATE_ROLLBACK_FAILED':
            sys.exit(
                "Rolling back for {} has failed. Please check the console.".format(
                    stack_details['StackName']))


def change_set_delete_waiter(change_set_id, cfn_client):
    """Boto3 does not have a waiter for deleting a change set, this is a custom one"""

    try:
        change_set_deletion_counter = 0
        change_set_deletion_bool = True

        while change_set_deletion_bool:
            change_set_details = cfn_client.describe_change_set(
                ChangeSetName=change_set_id)
            if change_set_details['Status'] in 'DELETE_COMPLETE':
                pass
                change_set_deletion_bool = False

            elif change_set_details['Status'] in 'FAILED':
                click.echo("\n{}".format(change_set_details['StatusReason']))
                sys.exit(
                    "Change set {} deletion has failed. Please check the console.".format(
                        change_set_details['StackName']))

            else:
                if change_set_deletion_counter == 120:
                    click.echo("\n{}".format(
                        change_set_details['StatusReason']))
                    sys.exit(
                        "Something went wrong while deleting the change set. Please check the console.")
                else:
                    change_set_deletion_counter += 1
                    time.sleep(15)

    except botocore.exceptions.ClientError:
        # Change set is already deleted therefore the waiter is no longer
        # needed.
        pass


def apply_changes(
        cfn_client,
        update_stack_name,
        past_failures,
        change_set_name,
        change_set):
    """Applies the change set and handles situations if something goes wrong"""

    click.echo("Executing change set: {}...".format(change_set_name))
    cfn_client.execute_change_set(
        ChangeSetName=change_set['Id'], StackName=update_stack_name)

    try:
        cfn_client.get_waiter('stack_update_complete').wait(
            StackName=update_stack_name)
    except botocore.exceptions.WaiterError:
        resource_failures = []
        for event in cfn_client.describe_stack_events(
                StackName=update_stack_name)['StackEvents']:
            if event['ResourceStatus'] in ['CREATE_FAILED', 'UPDATE_FAILED']:
                resource_failures.append(event)
        if resource_failures:
            for failures in resource_failures:
                if failures not in past_failures:
                    click.echo(
                        "{} has failed to be updated because: '{}'".format(
                            failures['LogicalResourceId'],
                            failures['ResourceStatusReason']))
        else:
            click.echo(
                "Please check console for why some resources failed to update.")

        stack_status = cfn_client.describe_stacks(StackName=update_stack_name)[
            'Stacks'][0]['StackStatus']
        if stack_status == 'UPDATE_ROLLBACK_FAILED':
            click.echo("Attempting to restore former state...")
            cfn_client.continue_update_rollback(StackName=update_stack_name)
            stack_continue_rollback_waiter(
                stack_name=update_stack_name, cfn_client=cfn_client)

        # Don't use sys.exit?
        sys.exit("Stopped update because of {}'s updating failure.".format(
            update_stack_name))


def change_log(changes, change_set):
    """Prints out all the possible changes to the CloudFormation stack"""

    data = []
    if change_set:
        for change in changes:
            try:
                replacement = change['ResourceChange']['Replacement']
            except KeyError:
                replacement = "None"

            try:
                physical_resource_id = change['ResourceChange']['PhysicalResourceId']
            except KeyError:
                physical_resource_id = "None"

            data.append(["Action: {}".format(change['ResourceChange']['Action']),
                         "Logical ID: {}".format(
                             change['ResourceChange']['LogicalResourceId']),
                         "Physical ID: {}".format(physical_resource_id),
                         "Resource Type: {}".format(
                             change['ResourceChange']['ResourceType']),
                         "Replacement: {}".format(replacement)])
    else:
        for change in changes:
            data.append(change)

    return data


def display_changes(changes, change_set):
    """Shows changes for  change set or deploying a new template"""
    if change_set:
        click.echo("\nChanges:")
        for change in change_log(changes=changes, change_set=change_set):
            # Dynamically gathers the length of each change in order to display
            # information better
            action = sorted([len(item[0]) for item in change])[-1]
            logical = sorted([len(item[1]) for item in change])[-1]
            physical = sorted([len(item[2]) for item in change])[-1]
            resource = sorted([len(item[3]) for item in change])[-1]
            replacement = sorted([len(item[4]) for item in change])[-1]

            click.echo(
                '{0: <{col1}}  {1:<{col2}}  {2:<{col3}}  {3:<{col4}}  {4:<{col5}}'.format(
                    *change,
                    col1=action,
                    col2=logical,
                    col3=physical,
                    col4=resource,
                    col5=replacement))
            click.echo("\t")

    else:
        click.echo("\nResources to be created:")
        for change in change_log(changes=changes, change_set=change_set):
            click.echo("\t{}".format(change))
