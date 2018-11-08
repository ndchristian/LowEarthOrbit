from __future__ import print_function

import os

import click


def format_path(**kwargs):
    """Creates a path type string"""
    objects = []
    for key, value in kwargs.items():
        objects.append(value)

    return '/'.join(objects)


def upload_templates(**kwargs):
    """Uploads files with the standard CloudFormation file extensions to the specific bucket in """

    upload_parameters = {}

    # Gets rid of excess forward slashes
    if 'prefix' in kwargs:
        prefix = kwargs['prefix']
        if prefix[-1] == "/":
            prefix = prefix.rstrip("/")
        if prefix[0] == "/":
            prefix = prefix.lstrip("/")
        upload_parameters.update({'prefix': prefix})

    bucket = kwargs['bucket']
    local_path = kwargs['local_path']
    session = kwargs['session']

    s3_client = session.client('s3')
    cfn_ext = ('.json', '.template', '.txt', 'yaml', 'yml')

    for file_object in os.listdir(local_path):
        # Needs a better if to only upload files with the LEO formatted names?
        if file_object.lower().endswith(cfn_ext):
            upload_parameters.update({'file_object': file_object})
            s3_client.upload_file(format_path(local_path=local_path, file_object=file_object),
                                  bucket, format_path(**upload_parameters))

            s3_client.get_waiter('object_exists').wait(Bucket=bucket,
                                                       Key=format_path(**upload_parameters))
            click.echo('Uploaded %s' % file_object)
