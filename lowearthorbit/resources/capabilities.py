def get(template_url, cfn_client):
    """Gets the needed capabilities for the CloudFormation stack """

    template_details = cfn_client.get_template_summary(TemplateURL=template_url)

    try:
        stack_capabilities = template_details['Capabilities']
    except KeyError:
        stack_capabilities = []

    return stack_capabilities
