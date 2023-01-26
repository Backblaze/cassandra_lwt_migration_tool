#!/usr/bin/env bash

PYTHON=${PYTHON:-python3}
VENV=${VENV:-$(pwd)/venv}

if [ -d ${VENV} ]; then
  exit 0  # all done
fi

set -x

${PYTHON} -m venv ${VENV}
. ${VENV}/bin/activate
${VENV}/bin/python -m pip install -U pip
${VENV}/bin/python -m pip install -e '.[dev]'