#!/bin/bash
PYTHON_VERSION=2.4

# FIXME put some of the below in a common routine
function checkout_version {
    local repo=$1
    version=${2:-python-2.4-to-2.7}
    echo Checking out $version on $repo ...
    (cd ../$repo && git checkout $version && pyenv local $PYTHON_VERSION) && \
	git pull
    return $?
}

export PATH=$HOME/.pyenv/bin/pyenv:$PATH
setup_pytracer_24_owd=$(pwd)
bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

rm -v */.python-version || true

git checkout python-2.4-to-2.7 && pyenv local $PYTHON_VERSION && git pull
cd $setup_pytracer_24_owd
