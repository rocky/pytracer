#!/bin/bash
# Check out 3.6-to-3.11 branch and dependant development branches

bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

PYTHON_VERSION=3.6

mydir=$(dirname $bs)
pytracer_owd=$(pwd)
cd $mydir
. ./checkout_common.sh
fulldir=$(readlink -f $mydir)

(cd $fulldir/.. && setup_version python-xdis python-3.6-to-3.10 )
cd $pytracer_owd
rm -v */.python-version 2>/dev/null || true
checkout_finish python-3.6-to-3.11
