#!/usr/bin/env bash

source config.conf

CURRDIR=${PWD##*/}
PREFIX="Projects/$CURRDIR"
LOCALPATH="$(pwd)"


if [ -z $1 ]
    then
        BUCKET="$BUCKET"

    elif [ $1 = "preprod" ]

        then

            BUCKET="$PREPROD_BUCKET"

    else

        echo ""
fi

if [ -z $1 ]
    then
        ENVIRONMENT="PROD"

    elif [ $1 = "preprod" ]

        then

            ENVIRONMENT="PREPROD"

    else

        echo ""
fi



prefix="\.\/"
SNAME=$(echo "$0" | sed -e "s/^$prefix//")

if  [ "deploy.sh" = $SNAME ]

    then
        source ./count
        i=`expr $i + 1`
        COUNT=$i

    else

        echo ""
fi


JOBIDENTIFIER="$CURRDIR"-"$ENVIRONMENT"-"$COUNT"

