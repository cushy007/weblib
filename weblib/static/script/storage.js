//
// Copyright 2021-2025, Johann Saunier
// SPDX-License-Identifier: AGPL-3.0-or-later
//
define(["log"], function(log) {

	let mStorage;

	function init() {
		console.log(`[storage] Initializing module...`);
		try {
			mStorage = window["localStorage"];
			const x = "__storage_test__";
			mStorage.setItem(x, x);
			mStorage.removeItem(x);
			console.log(`[storage] Initialized`);
			return true;
		} catch (err) {
			return (
				err instanceof DOMException &&
				(err.code === 22 ||
					err.code === 1014 ||
					err.name === "QuotaExceededError" ||
					err.name === "NS_ERROR_DOM_QUOTA_REACHED"
				) &&
				mStorage && mStorage.length !== 0
			);
		}
	}

	function getSet(name) {
		let item = mStorage.getItem(name);

		if (!item) {
			console.log(`[storage] Set '${name}' does not exist yet`);
			item = new Set();
			return item;
		} else {
			return new Set(JSON.parse(item));
		}
	}

	function addToSet(name, value) {
		let item = mStorage.getItem(name);

		if (!item) {
			console.log(`[storage] Set '${name}' does not exist yet -> creating it...`);
			item = new Set();
		} else {
			item = new Set(JSON.parse(item));
		}
		item.add(value);
		item = JSON.stringify([...item]);
		mStorage.setItem(name, item);
		console.log(`[storage] '${item}' added to set '${name}'`);
	}

	function deleteFromSet(name, value) {
		let item = mStorage.getItem(name);

		if (!item) {
			console.log(`[storage] Can't remove a value from empty set '${name}'`);
			return false;
		} else {
			item = new Set(JSON.parse(item));
			item.delete(value);
			mStorage.setItem(name, JSON.stringify([...item]));
			console.log(`[storage] '${value}' removed from set '${name}'`);
			return true;
		}
	}

	function clearSet(name) {
		let item = mStorage.getItem(name);

		if (!item) {
			console.log(`[storage] Can't clear the non existing set '${name}'`);
			return false;
		} else {
			mStorage.removeItem(name);
			console.log(`[storage] Set '${name}' has been cleared`);
			return true;
		}
	}

	return {
		init: init,
		getSet: getSet,
		addToSet: addToSet,
		deleteFromSet: deleteFromSet,
		clearSet: clearSet,
	}

});
