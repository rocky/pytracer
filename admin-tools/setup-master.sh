#!/bin/bash
# Check out master branch and dependent development master branches
bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

PYTHON_VERSION=3.12

mydir=$(dirname $bs)
pytracer_owd=$(pwd)
cd $mydir
. ./checkout_common.sh
checkout_finish master
