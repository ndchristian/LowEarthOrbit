from __future__ import print_function

import logging
import os

log = logging.getLogger(__name__)


def upload_templates(Bucket, Prefix, Session, LocalPath):
    """Uploads files with the standard CloudFormation file extentions to the specific bucket in """

    log.debug('Uploading templates to S3')

    s3_client = Session.client('s3')
    cfn_ext = ('.json', '.template', '.txt', 'yaml', 'yml')

    for file_object in os.listdir(LocalPath):
        if file_object.lower().endswith(cfn_ext) and file_object != 'config.json':
            s3_client.upload_file("{0:s}/{1:s}".format(LocalPath, file_object),
                                  Bucket, "{}/{}".format(Prefix, file_object))
            s3_client.get_waiter('object_exists').wait(Bucket=Bucket,
                                                       Key="{}/{}".format(Prefix, file_object))
            log.info('Uploaded {0:s} to {1:s}/{2:s}\n'.format(file_object, Bucket, Prefix))
            log.info('Uploaded %s', file_object)
