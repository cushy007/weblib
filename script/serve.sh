#!/bin/bash

. env.sh

if [ ${1:-""} = "selenium" ]; then
	export FLASK_PORT=${2}
	export DATABASE_NAME=${3}
elif [ ${1:-""} = "create_db" ]; then
	sudo -u postgres dropdb ${DATABASE_NAME} || true
	sudo -u postgres createdb --owner ${USER} -T template0 ${DATABASE_NAME}
elif [ ${1:-""} = "init_db" ]; then
	export CLEANUP_DB=1
fi

#export FLASK_ENV=development
#export FLASK_DEBUG=1

python3 ../weblib/weblib/server.py

