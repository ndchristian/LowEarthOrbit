import sys


def check(JobIdentifier):
    """Checks if the job identifier is up to CloudFormation's naming requirements."""

    if not JobIdentifier:
        sys.exit("job_identifier must have a value.")

    if not JobIdentifier.isalnum():
        sys.exit("The job identifier must be alpha-numeric.")

    return JobIdentifier
