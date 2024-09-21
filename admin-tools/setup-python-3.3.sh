#!/bin/bash
PYTHON_VERSION=3.3

# FIXME put some of the below in a common routine
function checkout_version {
    local repo=$1
    version=${2:-python-3.3-to-3.5}
    echo Checking out $version on $repo ...
    (cd ../$repo && git checkout $version && pyenv local $PYTHON_VERSION) && \
	git pull
    return $?
}

export PATH=$HOME/.pyenv/bin/pyenv:$PATH
setup_pytracer_33_owd=$(pwd)
bs=${BASH_SOURCE[0]}
if [[ $0 == $bs ]] ; then
    echo "This script should be *sourced* rather than run directly through bash"
    exit 1
fi

rm -v */.python-version || true

git checkout python-3.3-to-3.5 && pyenv local $PYTHON_VERSION && git pull
cd $setup_pytracer_33_owd
