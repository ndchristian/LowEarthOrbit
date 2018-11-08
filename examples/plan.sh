#!/usr/bin/env bash

source environ.sh

#echo $PROFILE
#echo $BUCKET
#echo $PREFIX
#echo $JOBIDENTIFIER
#echo $PARAMETERS

leo plan --bucket $BUCKET --prefix $PREFIX --job-identifier $JOBIDENTIFIER  --parameters "$PARAMETERS"

exit
