#!/bin/bash
GITHUB_DIR=pytracer
PYMODULE_NAME=tracer

# FIXME put some of the below in a common routine
function finish {
  cd $make_dist_pytracer_owd
}
make_dist_pytracer_owd=$(pwd)
trap finish EXIT

cd $(dirname ${BASH_SOURCE[0]})
if ! source ./pyenv-2.4-2.7-versions ; then
    exit $?
fi
if ! source ./setup-python-2.4.sh ; then
    exit $?
fi

cd ..
source $PYMODULE_NAME/version.py
if [[ ! -n $__version__ ]]; then
    echo "You need to set __version__ first"
    exit 1
fi
echo $__version__

for pyversion in $PYVERSIONS; do
    echo --- $pyversion ---
    if [[ ${pyversion:0:4} == "pypy" ]] ; then
	echo "$pyversion - PyPy does not get special packaging"
	continue
    fi
    if ! pyenv local $pyversion ; then
	exit $?
    fi

    rm -fr build
    python setup.py bdist_egg
    echo === $pyversion ===
done

echo "--- python 2.7 wheel ---"
pyenv local 2.7.18
python setup.py bdist_wheel
<<<<<<< HEAD
echo === $pyversion ===
=======
mv -v dist/${PYMODULE_NAME}-$__version__-{py2.py3,py2}-none-any.whl
>>>>>>> master

# PyPI can only have one source tarball.
# Tarballs can get created from the above setup, so make sure to remove them since we want
# the tarball from master.

python ./setup.py sdist

tarball=dist/${PYMODULE_NAME}-$__version__-tar.gz
if [[ -f $tarball ]]; then
<<<<<<< HEAD
    rm -v dist/${PYMOUDLE_NAME}-$__version__-tar.gz
=======
    rm -v dist/${PYMODULE_NAME}-$__version__-tar.gz
>>>>>>> master
fi
finish
