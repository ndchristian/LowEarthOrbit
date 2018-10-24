#!/usr/bin/env bash

source environ.sh

#echo $PROFILE
#echo $BUCKET
#echo $PREFIX
#echo $LOCALPATH

leo upload --bucket $BUCKET --prefix $PREFIX --local-path $LOCALPATH

exit