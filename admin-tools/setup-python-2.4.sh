#!/bin/bash
# Check out 2.4-to-2.7 branch and dependant development branches

bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

PYTHON_VERSION=2.4

git checkout python-2.4-to-2.7 && git pull && pyenv local $PYTHON_VERSION
