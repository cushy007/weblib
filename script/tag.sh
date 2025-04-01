#!/bin/bash

set -eu

. env.sh

VERSION=${1:-""}
VERSION_FILE="webapp/config.py"
WEBLIB_PATH="../weblib/"

if [ -z ${VERSION} ]; then
	VERSION=`python3 -c 'with open("webapp/config.py", "r") as f: exec(f.read()); new_v = APP_VERSION.split("."); new_v[-1] = str(int(new_v[-1]) + 1); print(".".join(new_v))'`
fi

if git tag | grep -q ${VERSION}; then
	echo "Version ${VERSION} alredy exists"
	exit 1
fi


`dirname "$0"`/make_messages.sh


function add_mo_to_vcs() {
	local dir=${1}

	pushd ${dir}
		find -name messages.mo -exec git add -f {} \;
		set +e
		git commit -m "Adding updated messages to VCS"
		set -e
	popd
}


function remove_mo_from_vcs() {
	local dir=${1}

	pushd ${dir}
		find -name messages.mo -exec git rm -f {} \;
		set +e
		git commit -m "Rollback .mo files"
		set -e
	popd
}


echo "########## Adding app messages objects to VCS..."
add_mo_to_vcs "."

echo "########## Adding lib messages objects to VCS..."
add_mo_to_vcs "../weblib/"

echo "########## Setting version $VERSION in $VERSION_FILE..."
sed -i "s/APP_VERSION.*$/APP_VERSION = \"${VERSION}\"/" ${VERSION_FILE}
git add ${VERSION_FILE}

echo "########## Taging application '$VERSION'..."
git commit -m "Tag ${VERSION}"
git tag ${VERSION}

pushd ${WEBLIB_PATH}
	TAG_NAME=${PROJECT_REPO_NAME}-${VERSION}
	echo "########## Taging weblib $TAG_NAME..."
	git tag ${TAG_NAME}
	git push origin ${TAG_NAME}
popd

echo "########## Rolling back app messages objects commits..."
remove_mo_from_vcs "."

echo "########## Rolling back app messages objects commits..."
remove_mo_from_vcs "../weblib/"

git push origin master
git push origin ${VERSION}

make messages

echo "########## TAG ${VERSION} done :)"
