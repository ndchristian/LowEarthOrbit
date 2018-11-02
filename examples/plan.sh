#!/usr/bin/env bash

source environ.sh

#echo $PROFILE
#echo $BUCKET
#echo $PREFIX

leo plan --bucket $BUCKET --prefix $PREFIX --job-identifier $JOBIDENTIFIER  --parameters $PARAMETERS

exit
