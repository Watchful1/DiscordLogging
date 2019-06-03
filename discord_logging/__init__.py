import logging.handlers
import time
import os
import configparser
import requests


_logger = None


class UTCFormatter(logging.Formatter):
	converter = time.gmtime


class WebhookHandler(logging.Handler):
	def __init__(self, webhook, username=None):
		super().__init__()
		self.webhook = webhook
		self.username = username

	def emit(self, record):
		data = {"content": self.format(record)}
		if self.username is not None:
			data['username'] = self.username
		return requests.post(self.webhook, data=data).content


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


def init_discord_logging(section_name):
	config = get_config()
	log = get_logger()
	formatter = logging.Formatter("%(levelname)s: %(message)s")

	logging_webhook = get_config_var(config, section_name, "logging_webhook")
	discord_logging_handler = WebhookHandler(logging_webhook, section_name)
	discord_logging_handler.setFormatter(formatter)
	discord_logging_handler.setLevel(logging.INFO)
	log.addHandler(discord_logging_handler)

	global_webhook = get_config_var(config, "global", "global_webhook")
	discord_global_handler = WebhookHandler(global_webhook, section_name)
	discord_global_handler.setFormatter(formatter)
	discord_global_handler.setLevel(logging.WARNING)
	log.addHandler(discord_global_handler)
