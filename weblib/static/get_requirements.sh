#!/bin/bash -xe

REQUIRE_JS="2.3.7"
DOM_READY="2.0.1"
BOOTSTRAP="5.3.3"
FONT_AWESOME="6.7.2"

SCRIPT_DIR="./script/external/"
CSS_DIR="./css/external/"
FONTAWESOME_CSS_DIR="./fontawesome/css/"
FONTAWESOME_WEBFONT_DIR="./fontawesome/webfonts/"

for dir in ${SCRIPT_DIR} ${CSS_DIR} ${FONT_AWESOME_DIR} ${FONTAWESOME_WEBFONT_DIR}; do
	rm -f ${dir}/*
done

wget -O ${SCRIPT_DIR}require.js https://requirejs.org/docs/release/${REQUIRE_JS}/minified/require.js

TMP_DIR=$(mktemp -d)

pushd ${TMP_DIR}
	wget https://github.com/requirejs/domReady/archive/refs/tags/${DOM_READY}.zip
	unzip ${DOM_READY}.zip
popd
mv ${TMP_DIR}/domReady-${DOM_READY}/domReady.js ${SCRIPT_DIR}

pushd ${TMP_DIR}
	wget https://github.com/twbs/bootstrap/releases/download/v${BOOTSTRAP}/bootstrap-${BOOTSTRAP}-dist.zip
	unzip bootstrap-${BOOTSTRAP}-dist.zip
popd
mv ${TMP_DIR}/bootstrap-${BOOTSTRAP}-dist/js/bootstrap.bundle.js ${SCRIPT_DIR}
mv ${TMP_DIR}/bootstrap-${BOOTSTRAP}-dist/js/bootstrap.bundle.js.map ${SCRIPT_DIR}
mv ${TMP_DIR}/bootstrap-${BOOTSTRAP}-dist/css/bootstrap.min.css.map ${CSS_DIR}
mv ${TMP_DIR}/bootstrap-${BOOTSTRAP}-dist/css/bootstrap.min.css ${CSS_DIR}

pushd ${TMP_DIR}
	wget https://use.fontawesome.com/releases/v${FONT_AWESOME}/fontawesome-free-${FONT_AWESOME}-web.zip
	unzip fontawesome-free-${FONT_AWESOME}-web.zip
popd
mv ${TMP_DIR}/fontawesome-free-${FONT_AWESOME}-web/css/fontawesome.min.css ${FONTAWESOME_CSS_DIR}
mv ${TMP_DIR}/fontawesome-free-${FONT_AWESOME}-web/css/solid.min.css ${FONTAWESOME_CSS_DIR}
mv ${TMP_DIR}/fontawesome-free-${FONT_AWESOME}-web/css/regular.min.css ${FONTAWESOME_CSS_DIR}
mv ${TMP_DIR}/fontawesome-free-${FONT_AWESOME}-web/webfonts/fa-regular-400.woff2 ${FONTAWESOME_WEBFONT_DIR}
mv ${TMP_DIR}/fontawesome-free-${FONT_AWESOME}-web/webfonts/fa-solid-900.woff2 ${FONTAWESOME_WEBFONT_DIR}

rm -rf ${TMP_DIR}

wget -O ${SCRIPT_DIR}/html5-qrcode.js https://github.com/mebjas/html5-qrcode/releases/download/v2.3.8/html5-qrcode.min.js
wget -O ${SCRIPT_DIR}/YConsole.js https://www.yorgsite.fr/experiments/YConsole/YConsole-compiled.js
