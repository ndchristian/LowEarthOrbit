import logging
import sys

log = logging.getLogger(__name__)


def check(JobIdentifier):
    """Checks if the job identifier is up to CloudFormation's naming requirements."""

    if not JobIdentifier:
        sys.exit("job_identifier must have a value.")

    if not JobIdentifier.isalnum():
        sys.exit("The job identifier must be alpha-numeric.")

    log.debug('Checked job identifier: %s' % JobIdentifier)

    return JobIdentifier
