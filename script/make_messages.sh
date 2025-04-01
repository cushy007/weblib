#!/bin/bash

# Doc: https://babel.pocoo.org/en/latest/cmdline.html

. env.sh

TRANSLATIONS_PATH_LIB=`pwd`/../"weblib/weblib/translations"
TRANSLATIONS_PATH_APP=`pwd`/"webapp/translations"
BABEL_CFG_PATH=`pwd`/script/babel.cfg
POT_FILE_LIB=`mktemp`
POT_FILE_APP=`mktemp`
POT_FILE_CAT=`mktemp`



if [ -d ${TRANSLATIONS_PATH_APP} ]; then
	echo "##### Extracing lib"
	pybabel extract --no-location --sort-output -F ${BABEL_CFG_PATH} -k _l -o ${POT_FILE_LIB} `pwd`/../weblib/weblib
	echo "##### Extracing app"
	pybabel extract --no-location --sort-output -F ${BABEL_CFG_PATH} -k _l -o ${POT_FILE_APP} `pwd`/webapp
	echo "##### Updating lib"
	pybabel update --no-fuzzy-matching -i ${POT_FILE_LIB} -d ${TRANSLATIONS_PATH_LIB} --domain messages # --omit-header
	echo "##### Updating app"
	pybabel update --no-fuzzy-matching -i ${POT_FILE_APP} -d ${TRANSLATIONS_PATH_APP} --domain messages
elif [ -d weblib ]; then
	echo "This command must not be launched onto weblib !"
	exit 1
else
	echo "##### First launch -> Create the translation tree"
	for language in en fr; do
		pybabel init -i ${POT_FILE_APP} -d ${TRANSLATIONS_PATH_APP} -l ${language}
	done
	exit 0
fi

#~ echo "##### Concatening lib and app messages DOES NOT WORK :("
#~ for language in en fr; do
	#~ output_file=${TRANSLATIONS_PATH_APP}/${language}/LC_MESSAGES/messages.po
	#~ rm -f ${output_file}
	#~ msgcat --to-code utf-8 --output-file ${output_file} \
		#~ ${TRANSLATIONS_PATH_LIB}/${language}/LC_MESSAGES/weblib.po \
		#~ ${TRANSLATIONS_PATH_APP}/${language}/LC_MESSAGES/webapp.po
#~ done

echo "##### Compiling lib and app messages"
pybabel compile -d ${TRANSLATIONS_PATH_LIB} --domain messages
pybabel compile -d ${TRANSLATIONS_PATH_APP} --domain messages

rm ${POT_FILE_LIB} ${POT_FILE_APP} ${POT_FILE_CAT}


echo "##### Removing creation date"
for path in $TRANSLATIONS_PATH_LIB $TRANSLATIONS_PATH_APP; do
	find $path -name "*.po" -exec sed -i '/POT-Creation-Date/d' {} \;
done

function check {
	local po_path=${1}/fr/LC_MESSAGES/messages.po
	echo -n "Checking ${TRANSLATIONS_PATH_LIB}... "
	set +u
	set -e
	if [ `msgattrib --untranslated ${po_path} | wc -l` != 0 ]; then
		echo "Error: missing translations:"
		msgattrib --untranslated ${po_path}
		geany ${po_path}
		exit 1
	fi
	echo "OK"
	set -u
}

echo "##### Entering check mode"
check ${TRANSLATIONS_PATH_LIB}
check ${TRANSLATIONS_PATH_APP}

