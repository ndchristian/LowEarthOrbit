import click


def remove_parameters(all_parameters, template_parameters):
    """Removes all parameters that the template does not need."""
    template_parameter_keys = [p['ParameterKey'] for p in template_parameters]
    template_parameters = []
    for parameter in all_parameters:
        if parameter['ParameterKey'] in template_parameter_keys:
            template_parameters.append(parameter)
    return template_parameters


def add_absent_parameters(parameters, template_parameters):
    """Adds all parameters that the template does need"""
    parameters_keys = [p['ParameterKey'] for p in parameters]
    for stack_parameter in template_parameters:
        if stack_parameter['ParameterKey'] not in parameters_keys:
            parameters.append({'ParameterKey': stack_parameter['ParameterKey'], 'ParameterValue': None})

    return parameters


def add_output_values(cfn_client, job_identifier, parameters):
    """Adds output values from previous stacks with the same job identifier to the parameter values"""
    output_counter = 0
    stack_names = sorted([stack['StackName'] for stack in cfn_client.describe_stacks()['Stacks'] if
                          "{}-".format(job_identifier) in stack['StackName']])
    for stack_name in stack_names:
        for stack in cfn_client.describe_stacks(StackName=stack_name)['Stacks']:
            if "{}-".format(job_identifier) in stack['StackName'] and "%02d" % output_counter in stack['StackName']:
                output_counter += 1
                try:
                    if stack['Outputs']:
                        for index_counter, parameter in enumerate(parameters):
                            for output in stack['Outputs']:
                                if parameter['ParameterKey'] == output['OutputKey']:
                                    parameters[index_counter] = {'ParameterKey': parameter['ParameterKey'],
                                                                 'ParameterValue': output['OutputValue']}

                except KeyError:
                    pass

    return parameters


def add_input_parameter_values(parameters):
    """If there is a parameter that does not have a value, it requests the user to add it"""
    for counter, parameter in enumerate(parameters):
        if parameter['ParameterValue'] is None:
            value = click.prompt("Please enter a value for {}: ".format(parameter['ParameterKey']), default="",
                                 show_default=False)
            if not value.strip():
                parameters.remove(parameter)
                continue

            else:
                parameters[counter] = {'ParameterKey': parameter['ParameterKey'],
                                       'ParameterValue': value}

    return parameters


def gather(session, key_object, parameters, bucket, job_identifier):
    """Gathers parameters from input and assigns values for the stack"""

    cfn_client = session.client('cloudformation')
    s3_client = session.client('s3')

    template_url = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': '{}'.format(bucket),
                                                            'Key': key_object},
                                                    ExpiresIn=60)

    template_summary = cfn_client.get_template_summary(TemplateURL=template_url)

    slimmed_parameters = remove_parameters(all_parameters=parameters,
                                           template_parameters=template_summary['Parameters'])

    full_parameters = add_absent_parameters(parameters=slimmed_parameters,
                                            template_parameters=template_summary['Parameters'])

    outputs_parameters = add_output_values(cfn_client=cfn_client,
                                           job_identifier=job_identifier,
                                           parameters=full_parameters)

    completed_parameters = add_input_parameter_values(parameters=outputs_parameters)

    return completed_parameters
