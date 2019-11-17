import logging.handlers
import time
import os
import configparser
import requests
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

				data = {"content": message[:2000]}
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
		max_size=1024*1024*16
):
	global _logger
	_logger = logger

	if level is None:
		if debug:
			level = logging.DEBUG
		else:
			level = logging.INFO

	if not os.path.exists(folder):
		os.makedirs(folder)

	log = logging.getLogger(logger)
	log.setLevel(level)
	log_formatter = UTCFormatter('%(asctime)s - %(levelname)s: %(message)s')

	log_stderr_handler = logging.StreamHandler()
	log_stderr_handler.setFormatter(log_formatter)
	log.addHandler(log_stderr_handler)

	log_file_handler = logging.handlers.RotatingFileHandler(
		os.path.join(folder, filename),
		maxBytes=max_size,
		backupCount=backup_count)
	log_file_handler.setFormatter(log_formatter)
	log.addHandler(log_file_handler)

	return log


def get_logger(init=False):
	global _logger
	if _logger is None:
		if init:
			return init_logging()
		else:
			raise ValueError("Logger not initialized")

	return logging.getLogger(_logger)


def set_level(level):
	get_logger().setLevel(level)


def get_config():
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
	if section not in config:
		raise ValueError(f"Section {section} not in config")

	if variable not in config[section]:
		raise ValueError(f"Variable {variable} not in section {section}")

	return config[section][variable]


def init_discord_logging(section_name, log_level, count_per_second=1):
	global discord_handlers
	config = get_config()
	log = get_logger()
	formatter = logging.Formatter("%(levelname)s: %(message)s")

	logging_webhook = get_config_var(config, section_name, "logging_webhook")
	discord_logging_handler = WebhookHandler(logging_webhook, section_name, count_per_second)
	discord_handlers.append(discord_logging_handler)
	discord_logging_handler.setFormatter(formatter)
	discord_logging_handler.setLevel(log_level)
	log.addHandler(discord_logging_handler)


def flush_discord():
	global discord_handlers
	for handler in discord_handlers:
		handler.sleep = True
		handler.emit(None)
		handler.sleep = False
