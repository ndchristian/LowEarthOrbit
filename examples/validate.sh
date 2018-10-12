#!/usr/bin/env bash

source config.conf

echo $PROFILE
echo $PRODBUCKET
echo $PREFIX

leo --profile $PROFILE validate --bucket $PRODBUCKET  --prefix $PREFIX

exit

