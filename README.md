A standardized logging handler for my reddit bots that supports logging to discord webhooks.

`init_logging()` creates a streamhandler that outputs to stdout and a rotating file handler that outputs to the specified folder.

`init_discord_logging("RemindMeBot", logging.WARNING)` initializes logging of warning and above level logs to the discord webhook specified by the `logging_webhook` variable in the provided `section_name` section of a `praw.ini` file. The same file that stores reddit login credentials for PRAW.

```
import discord_logging

log = discord_logging.init_logging()

log.info("Test message")

discord_logging.init_discord_logging("RemindMeBot", logging.WARNING)

log.warning("Warning message")

discord_logging.flush_discord()
```

I use pipenv for my bots, DiscordLogging can be installed with this command

```
pipenv install -e git+https://github.com/Watchful1/DiscordLogging.git#egg=discord-logging
```

If you use regular pip, it can be installed with

```
pip install git+https://github.com/Watchful1/DiscordLogging.git
```