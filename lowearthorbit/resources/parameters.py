import json
import logging
import os

import click

log = logging.getLogger(__name__)


def gather(s3_client, cfn_client, key_object, parameters, bucket, job_identifier):
    """Gathers parameters from input and assigns values for the stack"""

    log.debug('Gathering parameters')
    if not parameters:
        if os.path.exists(parameters):
            with open(parameters, 'r') as file_contents:
                parameters = json.loads(file_contents.read())

            log.debug('Loaded parameters from file')
        else:
            parameters = json.loads(parameters)
            log.debug('Loaded parameters from JSON input')

    template_url = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': '{}'.format(bucket),
                                                            'Key': key_object},
                                                    ExpiresIn=60)

    template_summary = cfn_client.get_template_summary(TemplateURL=template_url)

    for stack_parameter in template_summary['Parameters']:
        if stack_parameter['ParameterKey'] not in [p['ParameterKey'] for p in parameters]:
            parameters.append({'ParameterKey': stack_parameter['ParameterKey'], 'ParameterValue': None})
    log.debug('Grabbed parameters from template')

    output_counter = 0
    for stack_outputs in sorted([stacks for stacks in cfn_client.describe_stacks()['Stacks'] if
                                 "%s-" % job_identifier in stacks['StackName']],
                                key=lambda k: int(k['StackName'].split("-")[1])):
        stackname_output = stack_outputs['StackName']
        if "{}-".format(job_identifier) in stackname_output and "%02d" % output_counter in stackname_output:
            output_counter += 1
            for temp_parameters in cfn_client.get_template_summary(TemplateURL=template_url)['Parameters']:
                try:
                    if stack_outputs['Outputs']:
                        for outputs in stack_outputs['Outputs']:
                            if temp_parameters['ParameterKey'] == outputs['OutputKey']:
                                for counter, parameter in enumerate(parameters):
                                    if template_url['ParameterKey'] == parameter['ParameterKey']:
                                        parameters[counter] = {'ParameterKey': temp_parameters['ParameterKey'],
                                                               'ParameterValue': outputs['OutputValue']}
                except KeyError:
                    pass
        log.debug('Grabbed parameter values from stack outputs')

    for counter, parameter in enumerate(parameters):
        if parameter['ParameterValue'] is None:
            value = click.prompt("Please enter a value for {}: ".format(parameter['ParameterKey']))
            if value.replace(" ", "") == "":
                parameters.remove(parameter)
            else:
                parameters[counter] = {'ParameterKey': parameter['ParameterKey'],
                                       'ParameterValue': value}

    return parameters
