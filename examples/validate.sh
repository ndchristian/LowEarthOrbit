#!/usr/bin/env bash

source environ.sh

#echo $PROFILE
#echo $BUCKET
#echo $PREFIX

leo validate --bucket $BUCKET --prefix $PREFIX

exit

