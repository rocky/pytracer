#!/bin/bash
# Check out 2.4-to-2.7 branch and dependant development branches

bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

PYTHON_VERSION=2.4

export PATH=$HOME/.pyenv/bin/pyenv:$PATH
pytracer_owd=$(pwd)
mydir=$(dirname $bs)
cd $mydir
. ./checkout_common.sh
(cd $fulldir/.. && \
     setup_version python-spark python-2.4-to-2.7 && \
     setup_version python-xdis python-2.4-to-2.7 && \
     setup_version python-filecache python-2.4-to-2.7 && \
     setup_version pycolumnize python-3.0-to-3.5 && \
     setup_version python-uncompyle6 python-2.4-to-2.7 \
    )
cd $pytracer_owd
rm -v */.python-version 2>/dev/null || true

checkout_finish python-2.4-to-2.7
