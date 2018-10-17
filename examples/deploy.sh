#!/usr/bin/env bash

source environ.sh

#echo $COUNT
#echo $BUCKET
#echo $JOBIDENTIFIER
#echo $PARAMETERS

leo deploy --bucket $BUCKET --prefix $PREFIX --job-identifier $JOBIDENTIFIER --gated True --parameters $PARAMETERS

exit