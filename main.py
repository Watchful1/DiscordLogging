from discord_logging import discord_logging

log = discord_logging.init_logging(debug=True)

log.debug("debug")
log.info("info")
log.warning("warning")
log.error("error")
log.critical("critical")

discord_logging.init_discord_logging("Watchful1BotTest")

log.debug("debug2")
log.info("info2")
log.warning("warning2")
log.error("error2")
log.critical("critical2")

log.info("info3")
log.info("info4")
log.info("info5")
log.info("info6")
log.info("info7")
log.info("info8")
log.info("info9")
log.info("info10")
