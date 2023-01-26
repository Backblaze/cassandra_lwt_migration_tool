#!/usr/bin/env bash

PYTHON=${PYTHON:-python3}
VENV=$(pwd)/venv

if [ -z ${TWINE_USERNAME} ] || [ -z ${TWINE_PASSWORD} ]; then
  echo "Please make sure TWINE_USERNAME and TWINE_PASSWORD are set to use the publish script."
  exit -1
fi

if [ -z "$1" ]; then
  echo "USAGE: $0 [REPOSITORY]"
  exit -1
fi
PYPI_REPO="${1}"

set -e
. ${VENV}/bin/activate
PYTHON=${VENV}/bin/python

if [[ -d dist ]]; then
    rm -r dist
fi

${PYTHON} -m build

twine upload --verbose \
  --repository-url "${1}" \
  dist/*
