def get(template_url, session):
    """Gets the needed capabilities for the CloudFormation stack """

    cfn_client = session.client('cloudformation')

    template_details = cfn_client.get_template_summary(
        TemplateURL=template_url)

    try:
        stack_capabilities = template_details['Capabilities']
    except KeyError:
        # May not be needed since it's not required when creating or updating a
        # stack
        stack_capabilities = []

    return stack_capabilities
