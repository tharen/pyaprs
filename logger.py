import logging,logging.handlers

##TODO: put logging in its own module files
#setup global logging
LOG_FILENAME='aprs2kml.log'
logger = logging.getLogger('MyLogger')
logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(
              LOG_FILENAME, maxBytes=500*1024, backupCount=5)
formatter=logging.Formatter("%(levelname)s - %(module)s.%(funcName)s(%(lineno)s) - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

sh=logging.StreamHandler()
sh.setLevel(logging.INFO)
logger.addHandler(sh)
