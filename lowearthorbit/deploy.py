from lowearthorbit.resources.create import create_stack
from lowearthorbit.resources.update import update_stack


def deploy_type(stack_name, cfn_client):
    """Checks if the CloudFormation stack should be created or updated"""

    for stack in cfn_client.describe_stacks()['Stacks']:
        cfn_stack_name = stack['StackName'].split('-')
        leo_stack_name = stack_name.split('-')
        try:
            if cfn_stack_name[0] == leo_stack_name[0] and cfn_stack_name[2] == leo_stack_name[2]:
                if stack['StackStatus'] in ('CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE'):
                    return {'Update': True, 'UpdateStackName': stack['StackName']}
        except IndexError:  # For non-Leo stack names
            pass

    return {'Update': False}


def deploy_templates(session, bucket, prefix, job_identifier,parameters, gated, tags):
    """Creates or updates CloudFormation stacks"""

    s3_client = session.client('s3')
    cfn_client = session.client('cloudformation')

    cfn_ext = ('.json', '.template', '.txt', '.yaml', '.yml')

    stack_archive = []

    stack_counter = 0
    for object in s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix
    )['Contents']:
        if object['Key'].endswith(cfn_ext) and object['Key'].split('/')[-1].startswith('%02d' % stack_counter):
            template_url = s3_client.generate_presigned_url('get_object',
                                                            Params={'Bucket': bucket,
                                                                    'Key': object['Key']},
                                                            ExpiresIn=60)
            template_summary = cfn_client.get_template_summary(TemplateURL=template_url)
            stack_name = "{}-{}".format(job_identifier, str(object['Key'].split('/')[-1]).rsplit('.', 1)[0])

            check = deploy_type(stack_name=stack_name,
                                cfn_client=cfn_client)

            if check['Update']:
                update_stack(update_stack_name=check['UpdateStackName'],
                             template_url=template_url,
                             session=session,
                             key_object=object['Key'],
                             bucket=bucket,
                             job_identifier=job_identifier,
                             parameters=parameters,
                             tags=tags,
                             gated=gated)

                stack_archive.append({'StackName': stack_name})


            else:
                create_stack(template_url=template_url,
                             template_details=template_summary,
                             parameters=parameters,
                             bucket=bucket,
                             session=session,
                             cfn_client=cfn_client,
                             s3_client=s3_client,
                             key_object=object['Key'],
                             tags=tags,
                             job_identifier=job_identifier)

                stack_archive.append({'StackName': stack_name})

            stack_counter += 1
