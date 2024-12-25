# -*- coding: utf-8 -*-
from utils.client import BotPool
import utils.logger
_log = utils.logger.getLogger(__name__)
_log.info("Booting up...")

pool = BotPool()

pool.setup()
