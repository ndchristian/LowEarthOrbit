#!/usr/bin/env bash

source config.conf

echo $PRODBUCKET
echo $JOB_IDENTIFIER
echo $PARAMETERS

leo deploy --bucket $PRODBUCKET --job-identifier $JOB_IDENTIFIER --gated True --parameters $PARAMETERS

exit