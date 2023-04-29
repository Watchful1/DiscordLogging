import logging.handlers
import time
import os
import configparser
import requests
import re
from datetime import datetime


_logger = None
discord_handlers = []


class UTCFormatter(logging.Formatter):
	converter = time.gmtime


class WebhookHandler(logging.Handler):
	def __init__(self, webhook, username=None, count_per_second=10):
		super().__init__()
		self.webhook = webhook
		self.username = username
		self.queue = []
		self.remaining = 5
		self.reset = None
		self.last_sent = None
		self.count_sent = 0
		self.count_per_second = count_per_second
		self.sleep = False

	def emit(self, record):
		try:
			now = datetime.utcnow().replace(microsecond=0)
			if record is None:
				message = None
			else:
				message = self.format(record)

			if self.sleep:
				if self.remaining <= 0:
					time.sleep(max(1, (self.reset - now).seconds))
					now = datetime.utcnow().replace(microsecond=0)
				self.count_sent = 0

			if self.reset is not None and self.reset < now:
				self.remaining = 5

			if self.last_sent is not None and self.last_sent < now:
				self.count_sent = 0

			if self.remaining > 0 and self.count_sent < self.count_per_second:
				if len(self.queue):
					if message is not None:
						self.queue.append(message)
					message = '\n'.join(self.queue)
					self.queue = []

				if message is None or message == "":
					return True

				replaced_message = re.sub(r"([ur]/[\w-]+)([^\w/])", r"[\1](<https://www.reddit.com/\1>)\2", message)

				data = {"content": replaced_message[:2000]}
				if self.username is not None:
					data['username'] = self.username
				result = requests.post(self.webhook, data=data)

				if 'X-RateLimit-Remaining' in result.headers:
					self.remaining = int(result.headers['X-RateLimit-Remaining'])
				if 'X-RateLimit-Reset' in result.headers:
					self.reset = datetime.utcfromtimestamp(int(result.headers['X-RateLimit-Reset']))
				self.last_sent = now
				self.count_sent += 1

				if not result.ok:
					self.queue.append(message)
					return False
			else:
				if message is not None:
					self.queue.append(message)
				return False
			return True
		except Exception:
			return False


def init_logging(
		debug=False,
		level=None,
		folder="logs",
		filename="bot.log",
		logger="bot",
		backup_count=5,
		max_size=1024*1024*16,
		format_string='%(asctime)s - %(levelname)s: %(message)s',
		add_trace=False
):
	"""Initialize and return a python logger. Creates a stream handler that outputs to stdout and a rotating file handler

	:param debug: Flag to set the log level to debug. Overriden by level argument if passed
	:param level: The log level to set the logger to. Defaults to INFO if not passed
	:param folder: The folder name to write log files to
	:param filename: The file name to use for the log files
	:param logger: The logger name. Only relevant to make sure it doesn't conflict with another existing logger
	:param backup_count: The number of rotated log files to keep
	:param max_size: The max size, in bytes, that log files can get to before being rotated. Defaults to 16 megabytes
	:param format_string: The format string for log messages
	:param add_trace: Add a trace log level
	:return: The logger object
	"""
	global _logger
	_logger = logger

	if level is None:
		if debug:
			level = logging.DEBUG
		else:
			level = logging.INFO

	log = logging.getLogger(logger)

	if add_trace:
		trace_level = logging.DEBUG - 5
		def logForLevel(self, message, *args, **kwargs):
			if self.isEnabledFor(trace_level):
				self._log(trace_level, message, args, **kwargs)

		def logToRoot(message, *args, **kwargs):
			logging.log(trace_level, message, *args, **kwargs)

		logging.addLevelName(trace_level, "TRACE")
		setattr(logging, "TRACE", trace_level)
		setattr(logging.getLoggerClass(), "trace", logForLevel)
		setattr(logging, "trace", logToRoot)

	log.setLevel(level)
	log_formatter = UTCFormatter(format_string)

	log_stderr_handler = logging.StreamHandler()
	log_stderr_handler.setFormatter(log_formatter)
	log.addHandler(log_stderr_handler)

	if folder is not None:
		if not os.path.exists(folder):
			os.makedirs(folder)
		log_file_handler = logging.handlers.RotatingFileHandler(
			os.path.join(folder, filename),
			maxBytes=max_size,
			backupCount=backup_count)
		log_file_handler.setFormatter(log_formatter)
		log.addHandler(log_file_handler)

	return log


def get_logger(init=False):
	"""Gets and returns the global log object.

	:param init: If the logger is not initialized, initialize it with default values
	:return: The logger object
	"""
	global _logger
	if _logger is None:
		if init:
			return init_logging()
		else:
			raise ValueError("Logger not initialized")

	return logging.getLogger(_logger)


def set_level(level):
	"""Shortcut to set the default loggers log level.

	:param level: The log level to set to
	"""
	get_logger().setLevel(level)


def get_config():
	"""Finds and loads a praw.ini file. Copied from PRAW's source code

	:return: The loaded config file
	"""
	config = configparser.ConfigParser()
	if 'APPDATA' in os.environ:  # Windows
		os_config_path = os.environ['APPDATA']
	elif 'XDG_CONFIG_HOME' in os.environ:  # Modern Linux
		os_config_path = os.environ['XDG_CONFIG_HOME']
	elif 'HOME' in os.environ:  # Legacy Linux
		os_config_path = os.path.join(os.environ['HOME'], '.config')
	else:
		raise FileNotFoundError("Could not find config")
	os_config_path = os.path.join(os_config_path, 'praw.ini')
	config.read(os_config_path)

	return config


def get_config_var(config, section, variable):
	"""Takes a config object and pulls out the passed in section and variable

	:param config: A configparser object
	:param section: The section in the config to look under
	:param variable: The variable name to find
	:return: The config value found
	"""
	if section not in config:
		raise ValueError(f"Section {section} not in config")

	if variable not in config[section]:
		raise ValueError(f"Variable {variable} not in section {section}")

	return config[section][variable]


def init_discord_logging(section_name, log_level, count_per_second=1, logging_webhook=None):
	"""Initializes output of log messages to a discord webhook.

	By default, this pulls the webhook url from a praw.ini file, but that can be overridden.

	:param section_name: The praw.ini config section name to pull the webhook from. Also sets the name the webhook uses
	:param log_level: The log level to start sending messages to discord at
	:param count_per_second: Webhooks are rate limited, this sets the maximum number of messages to send per second. Default 1
	:param logging_webhook: The webhook to emit to. If left as None, pulls from the praw.ini file instead
	"""
	global discord_handlers
	config = get_config()
	log = get_logger()
	formatter = logging.Formatter("%(levelname)s: %(message)s")

	if logging_webhook is None:
		logging_webhook = get_config_var(config, section_name, "logging_webhook")
	discord_logging_handler = WebhookHandler(logging_webhook, section_name, count_per_second)
	discord_handlers.append(discord_logging_handler)
	discord_logging_handler.setFormatter(formatter)
	discord_logging_handler.setLevel(log_level)
	log.addHandler(discord_logging_handler)


def flush_discord():
	"""Since discord webhooks are rate limited, the logger caches messages if they are sent in quick succession.
	This method flushes out the cache, waiting as long as necessary to finish sending the messages."""
	global discord_handlers
	for handler in discord_handlers:
		handler.sleep = True
		handler.emit(None)
		handler.sleep = False
