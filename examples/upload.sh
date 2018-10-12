#!/usr/bin/env bash

source config.conf

#echo $PRODBUCKET
#echo $PREFIX
#echo $LOCALPATH

leo upload --bucket $BUCKET --prefix $PREFIX --localpath $LOCALPATH

exit