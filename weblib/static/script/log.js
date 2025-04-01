//
// Copyright 2021-2025, Johann Saunier
// SPDX-License-Identifier: AGPL-3.0-or-later
//
define([], function() {

	let mLevels = {
		"debug": 0,
		"info": 1,
		"warn": 2,
		"error": 3,
	};
	let mLevelName;
	let mLevel;

	function init(levelName) {
		mLevelName = (levelName === undefined) ? "info" : levelName;
		mLevel = mLevels[mLevelName];
	}

	function _log(levelName, text, object) {
		if (object === undefined) {
			console[levelName](text);
		} else {
			//console.group(text);
			console[levelName](text, object);
			//console.groupEnd();
		}
	}

	function debug(text, object) {
		if (mLevel < 1) {
			_log("log", text, object);
		}
	}

	function info(text, object) {
		if (mLevel < 2) {
			_log("info", text, object);
		}
	}

	function warning(text, object) {
		if (mLevel < 3) {
			_log("warn", text, object);
		}
	}

	function error(text, object) {
		if (mLevel < 4) {
			_log("error", text, object);
		}
	}

	return {
		init: init,
		debug: debug,
		info: info,
		warning: warning,
		error: error,
	}

});
