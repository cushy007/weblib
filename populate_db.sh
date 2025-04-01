#!/bin/bash
set -x

. env.sh

FROM=${1:-backup}
HOST_TO=${2:-server-vm}

DB_USER=www-${PROJECT_REPO_NAME}
BACKUP_TARBALL=$(ls -t -1 /media/data/srv_backup/git/${PROJECT_REPO_NAME}* | head -n 1)

echo "##### Dumping DB from $FROM..."
if [ ${FROM} = "desktop" ]; then
	# FIXME still needed ???
	DUMP_PATH="/tmp/${DATABASE_NAME}.sqlc"
	sudo -u postgres pg_dump -Fc --no-owner --file ${DUMP_PATH} ${DATABASE_NAME}
	scp ${DUMP_PATH} ${HOST_TO}:${DUMP_PATH}
	ssh ${HOST_TO} sudo chmod a+r ${DUMP_PATH}
else
	sudo tar -C /tmp -xf ${BACKUP_TARBALL}
fi

echo "##### Restoring DB to $HOST_TO..."
if [ ${HOST_TO} = "desktop" ]; then
	DUMP_PATH="/tmp/${DATABASE_NAME}.sql"
	sed -i '/default_table_access_method/d' ${DUMP_PATH}
	sed -i "s/$DB_USER/$USER/g" ${DUMP_PATH}
	sudo -u postgres dropdb ${DATABASE_NAME} | true
	sudo -u postgres createdb --owner ${USER} -T template0 ${DATABASE_NAME}
	[[ -f populate_db_hook.sh ]] && . populate_db_hook.sh
	#sudo -u ${USER} pg_restore --dbname ${DATABASE_NAME} ${DUMP_PATH} | true
	sudo -u postgres psql --set ON_ERROR_STOP=on ${DATABASE_NAME} < ${DUMP_PATH}
else
	DUMP_PATH="/tmp/${DATABASE_NAME}.sqlc"
	scp ${DUMP_PATH} ${HOST_TO}:${DUMP_PATH}
	ssh ${HOST_TO} sudo chmod a+r ${DUMP_PATH}
	ssh ${HOST_TO} sudo systemctl stop apache2
	ssh ${HOST_TO} sudo -u postgres dropdb ${DATABASE_NAME} || true
	ssh ${HOST_TO} sudo -u postgres createdb --owner ${DB_USER} -T template0 ${DATABASE_NAME}
	[[ -f populate_db_hook.sh ]] && . populate_db_hook.sh
	ssh ${HOST_TO} sudo -u ${DB_USER} pg_restore --dbname ${DATABASE_NAME} ${DUMP_PATH} || true
	ssh ${HOST_TO} sudo systemctl start apache2
fi
