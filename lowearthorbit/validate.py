from __future__ import print_function

import logging

import botocore

log = logging.getLogger(__name__)


def validate_templates(bucket, prefix, session):
    """"Attempts to validate every file in the bucket subdirectory with every known CloudFormation extension."""

    log.debug("Validating templates")

    s3_client = session.client('s3')
    cf_client = session.client('cloudformation')
    cfn_ext = ('.json', '.template', '.txt', 'yaml', 'yml')

    validation_errors = []
    for object in s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=prefix
    )['Contents']:
        if object['Key'].endswith(cfn_ext):
            template_url = s3_client.generate_presigned_url('get_object',
                                                            Params={'Bucket': bucket,
                                                                    'Key': object['Key']},
                                                            ExpiresIn=60)
            try:
                cf_client.validate_template(TemplateURL=template_url)
                log.info("Validated %s", object['Key'])

            except botocore.exceptions.ClientError as e:
                validation_errors.append({'Template': object['Key'], 'Error': e})

    return validation_errors
