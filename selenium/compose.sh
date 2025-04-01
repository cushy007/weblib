#!/bin/bash

set -eu

export MY_TIMEZONE="Europe/Paris"

RESOURCES_DIR=$(pwd)/"../weblib/test/func/resources"
chmod a+rx ${RESOURCES_DIR}
chmod a+r ${RESOURCES_DIR}/*

pushd $(dirname $0)

DOCKER_IMAGE="selenium/standalone-chrome:100.0"
DOCKER_TAG_NAME="selenium-standalone-chrome:custom"
DOCKER_CONTAINER="selenium-standalone-chrome"


function is_container_running()
{
	docker container inspect $DOCKER_CONTAINER &> /dev/null
	return $?
}


function docker_init()
{
	set +e
	docker kill ${DOCKER_CONTAINER} &> /dev/null
	docker kill ${DOCKER_CONTAINER}"-2" &> /dev/null
	docker image build --build-arg IMAGE=${DOCKER_IMAGE} -t ${DOCKER_TAG_NAME} .
	set -e
}


function docker_start()
{
	echo "------- Be aware that IP Forwarding is mandatory --------"
	echo "$ sudo sysctl net.ipv4.conf.all.forwarding=1"
	echo "$ sudo systemctl stop nftables.service"
	echo "---------------------------------------------------------"

	is_container_running && return

	docker run \
		--detach \
		--shm-size="2g" \
		--env TZ=${MY_TIMEZONE} \
		--env LANGUAGE=fr_FR.UTF-8 \
		--env LANG=fr_FR.UTF-8 \
		--env LANG_WHERE=FR \
		--env LANG_WHICH=fr \
		--volume ${RESOURCES_DIR}:/home/seluser/resources \
		-p 4444:4444 -p 7900:7900 \
		--rm --name ${DOCKER_CONTAINER} \
		${DOCKER_TAG_NAME}

	docker run \
		--detach \
		--shm-size="2g" \
		--env TZ=${MY_TIMEZONE} \
		--env LANGUAGE=fr_FR.UTF-8 \
		--env LANG=fr_FR.UTF-8 \
		--env LANG_WHERE=FR \
		--env LANG_WHICH=fr \
		--volume ${RESOURCES_DIR}:/home/seluser/resources \
		-p 4445:4444 -p 7901:7900 -p 5901:5900 \
		--rm --name ${DOCKER_CONTAINER}"-2" \
		${DOCKER_TAG_NAME}

	sleep 10
}


function docker_stop()
{
	docker stop ${DOCKER_CONTAINER} &> /dev/null || true
	docker stop ${DOCKER_CONTAINER}"-2" &> /dev/null || true
}


while getopts "isr" flag; do
	case $flag in
		i) OPT_INIT=1;;
		s) OPT_START=1;;
		r) OPT_RESTART=1;;
	esac
done

[ -v OPT_INIT ] && docker_init
[ -v OPT_START ] && docker_start
if [ -v OPT_RESTART ]; then
	docker_stop
	docker_start
fi

popd
