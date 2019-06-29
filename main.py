import discord_logging
import requests
from datetime import datetime
import time


log = discord_logging.init_logging(debug=True)

discord_logging.init_discord_logging("Watchful1BotTest", 1)

log.info("Test1")
log.info("Test2")
log.info("Test3")
log.info("Test4")
time.sleep(2)
log.info("Test5")
log.info("Test6")
log.info("Test7")
log.info("Test8")
log.info("Test9")
log.info("Test10")
time.sleep(2)
log.info("Test11")
log.info("Test12")
log.info("Test13")
discord_logging.flush_discord()
