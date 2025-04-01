#!/bin/bash -x

. env.sh

reset

PYTEST_OPTIONS="-W ignore::DeprecationWarning"
PYTEST_OPTIONS="${PYTEST_OPTIONS} -vvv"
#~ PYTEST_OPTIONS="${PYTEST_OPTIONS} --full-trace"

set +u
if [ "$1" = "unit" ]; then
	TEST_TO_LAUNCH=${2:-test/unit/}
elif [ "$1" = "func" ]; then
	selenium/compose.sh -s
	TEST_TO_LAUNCH=${2:-test/func/}
elif [ "$1" = "tests" ]; then
	selenium/compose.sh -s
	TEST_TO_LAUNCH=${2:-"test/unit/ test/func/"}
else
	exit 1
fi
set -u

python3 -m pytest ${PYTEST_OPTIONS} ${TEST_TO_LAUNCH}

