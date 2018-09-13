def get(template_url, session):
    """Gets the needed capabilities for the CloudFormation stack """

    template_details = session.client('cloudformation').get_template_summary(TemplateURL=template_url)

    try:
        stack_capabilities = template_details['Capabilities']
    except KeyError:
        stack_capabilities = []

    return stack_capabilities
