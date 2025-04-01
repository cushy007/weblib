#
# Copyright 2021-2025, Johann Saunier
# SPDX-License-Identifier: AGPL-3.0-or-later
#
import logging
import os
import shlex
import sys
import tempfile
import time
from configparser import ConfigParser, NoSectionError
from functools import wraps
from logging import Formatter, handlers
from os import close, write
from os.path import expanduser, join
from subprocess import PIPE, STDOUT, Popen

_LOGGER = logging.getLogger(__name__)


__STREAM_HANDLER = None
__FILE_HANDLER = None


def log_init(logger_name, directory="~", level=logging.INFO):
	"""
	Create a console logger and a file logger named after *logger_name* and located in *directory*. If *directory* is set to None then no file is created.

	"""
	global __STREAM_HANDLER
	global __FILE_HANDLER

	root_logger = logging.getLogger()

	__STREAM_HANDLER = logging.StreamHandler()
	__STREAM_HANDLER.setFormatter(Formatter("%(asctime)s - %(name)s - %(levelname)8s - %(message)s"))
	__STREAM_HANDLER.setLevel(level)
	root_logger.addHandler(__STREAM_HANDLER)

	if directory is not None:
		filepath = expanduser(join(directory, ".%s.log" % logger_name))
		__FILE_HANDLER = handlers.RotatingFileHandler(filepath, maxBytes=1 * 1024 * 1024, backupCount=3)
		__FILE_HANDLER.setFormatter(Formatter("%(asctime)s - %(name)s - %(levelname)8s - %(message)s"))
		__FILE_HANDLER.setLevel(level)
		root_logger.addHandler(__FILE_HANDLER)

	root_logger.setLevel(logging.DEBUG)

	return root_logger


def get_config(filepath="~/.jspython.conf", section='DEFAULT'):
	config = ConfigParser()
	try:
		config.read(expanduser(filepath), encoding='utf8')
	except NoSectionError:
		_LOGGER.exception("section %s not found in %s", section, filepath)
		raise

	return dict(config.items(section))


def profiled(functor):

	@wraps(functor)
	def wrapper(*args, **kwargs):
		_LOGGER.info("--> entering profiled function %s(%s, %s)", functor.__name__, args, kwargs)
		start_time = time.time()
		ret = functor(*args, **kwargs)
		_LOGGER.info("<-- execution of %s(%s, %s) took %s seconds", functor.__name__, args, kwargs, time.time() - start_time)
		return ret

	return wrapper


# pylint: enable=C0111
def mkstemp(suffix='', prefix='tmp', dir=None, text=None):
	"""
	Securely creates a temporary file. Optionaly initializes it with some text, closes it and returns the full path to
	the file.

	"""
	hd, filepath = tempfile.mkstemp(suffix, prefix, dir, text=False)
	if text:
		write(hd, text.encode('utf-8'))
	close(hd)

	return filepath


class _Pipe(object):

	def __init__(self, truth_value, shell):
		self._truth_value = truth_value
		self._shell = shell

	def __nonzero__(self):
		return self._truth_value

	def __bool__(self):
		return self._truth_value

	def __or__(self, other):
		stdin = "\n".join(self._shell.stdout).encode('utf8')
		return self._shell.execute(other, stdin=stdin)


# pylint: enable=C0111
class Shell(object):
	"""
	Provides a shell like interface

	"""
	def __init__(self, new_line_char='\n', env_vars=None, cwd=None):
		self.new_line_char = new_line_char
		self._env_vars = env_vars or {}
		self._cwd = cwd
		self._retcode = None
		self._stdout = []
		self._stderr = []

	def _buf_to_list(self, buf):
		return [line.strip(self.new_line_char) for line in buf.split(self.new_line_char) if line]

	def __execute(self, cmd, stdin, split_stdout_stderr, capture, timeout):
		env = os.environ
		env.update(self._env_vars)
		if not isinstance(cmd, (list, tuple)):
			cmd = shlex.split(cmd)
		try:
			if capture:
				proc = Popen(
					cmd,
					shell=False,
					stdin=PIPE if stdin else None,
					stdout=PIPE,
					stderr=PIPE if split_stdout_stderr else STDOUT,
					env=env,
					cwd=self._cwd
				)
				communicate_kwargs = {'input': stdin}
				if sys.version_info[:3] >= (3, 3):
					communicate_kwargs.update({'timeout': timeout})
				elif timeout:
					_LOGGER.warning("process timeout handled only in Python 3")
				stdout, stderr = proc.communicate(**communicate_kwargs)
				stdout = stdout.decode('utf8')
				stderr = "" if not stderr else stderr.decode('utf8')
				self._retcode = proc.returncode
				self._stdout = self._buf_to_list(stdout)
				self._stderr = self._buf_to_list(stderr)
			else:
				self._retcode = Popen(cmd, shell=False, env=env).wait()
		except OSError:
			_LOGGER.exception("System error")
			self._retcode = 1
			self._stdout = self._stderr = []
			if split_stdout_stderr:
				self._stderr = ["ooops"]

	def execute(self, cmd, stdin=None, split_stdout_stderr=False, capture=True, timeout=None):
		"""
		Executes a command and returns True in case of success. The command's return code is stored in the retcode attribute.
		If *cmd* is given as an iterable, each item should be a minimal unit (eg: ["ls", "-l", "/path/with spaces/"])

		"""
		self.__execute(cmd, stdin, split_stdout_stderr, capture, timeout)
		return _Pipe(self._retcode == 0, self)

	def execute_get_stdout(self, cmd, stdin=None, timeout=None):
		"""
		Executes a command and returns stdout as a list. This is a shortcut for::

			def get_cmd_stdout(sh, cmd):
				sh.execute("ls")
				return sh.stdout

		see :meth:`execute`

		"""
		self.__execute(cmd, stdin=stdin, split_stdout_stderr=False, capture=True, timeout=timeout)
		return self._stdout

	@property
	def retcode(self):
		"""
		The command's return code.

		"""
		return self._retcode

	@property
	def stdout(self):
		"""
		The last command's standard output as a list of lines.

		"""
		return self._stdout

	@property
	def stderr(self):
		"""
		The last command's standard error as a list of lines.

		"""
		return self._stderr

	def set_cwd(self, cwd):
		self._cwd = cwd

	def get_cwd(self):
		return self._cwd

