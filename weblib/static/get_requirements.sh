#!/bin/bash -xe

REQUIRE_JS=2.3.7
DOM_READY=2.0.1
BOOTSTRAP=5.3.3
FONT_AWESOME=6.7.2

wget -O ./script/external/require.js https://requirejs.org/docs/release/${REQUIRE_JS}/minified/require.js

TMP_DIR=$(mktemp -d)

pushd ${TMP_DIR}
	wget https://github.com/requirejs/domReady/archive/refs/tags/${DOM_READY}.zip
	unzip ${DOM_READY}.zip
popd
mv ${TMP_DIR}/domReady-${DOM_READY}/domReady.js ./script/external/

pushd ${TMP_DIR}
	wget https://github.com/twbs/bootstrap/releases/download/v${BOOTSTRAP}/bootstrap-${BOOTSTRAP}-dist.zip
	unzip bootstrap-${BOOTSTRAP}-dist.zip
popd
mv ${TMP_DIR}/bootstrap-${BOOTSTRAP}-dist/js/bootstrap.bundle.js ./script/external/bootstrap.bundle.js
mv ${TMP_DIR}/bootstrap-${BOOTSTRAP}-dist/js/bootstrap.bundle.js.map ./script/external/bootstrap.bundle.js.map
mv ${TMP_DIR}/bootstrap-${BOOTSTRAP}-dist/css/bootstrap.min.css.map ./css/external/bootstrap.min.css.map
mv ${TMP_DIR}/bootstrap-${BOOTSTRAP}-dist/css/bootstrap.min.css ./css/external/bootstrap.min.css

pushd ${TMP_DIR}
	wget https://use.fontawesome.com/releases/v${FONT_AWESOME}/fontawesome-free-${FONT_AWESOME}-web.zip
	unzip fontawesome-free-${FONT_AWESOME}-web.zip
popd
mv ${TMP_DIR}/fontawesome-free-${FONT_AWESOME}-web/css/fontawesome.min.css ./fontawesome/css/fontawesome.min.css
mv ${TMP_DIR}/fontawesome-free-${FONT_AWESOME}-web/css/solid.min.css ./fontawesome/css/solid.min.css
mv ${TMP_DIR}/fontawesome-free-${FONT_AWESOME}-web/css/regular.min.css ./fontawesome/css/regular.min.css
mv ${TMP_DIR}/fontawesome-free-${FONT_AWESOME}-web/webfonts/fa-regular-400.woff2 ./fontawesome/webfonts/fa-regular-400.woff2
mv ${TMP_DIR}/fontawesome-free-${FONT_AWESOME}-web/webfonts/fa-solid-900.woff2 ./fontawesome/webfonts/fa-solid-900.woff2

rm -rf ${TMP_DIR}

wget -O ./script/external/html5-qrcode.js https://github.com/mebjas/html5-qrcode/releases/download/v2.3.8/html5-qrcode.min.js
wget -O ./script/external/YConsole.js https://www.yorgsite.fr/experiments/YConsole/YConsole-compiled.js
