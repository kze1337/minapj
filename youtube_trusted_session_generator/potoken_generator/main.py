import asyncio
import logging
from pathlib import Path
from typing import Optional
from .extractor import PotokenExtractor, TokenInfo

logger = logging.getLogger(__name__)

async def run(loop: asyncio.AbstractEventLoop,
                update_interval: int,
                browser_path: Optional[Path] = None) -> Optional[TokenInfo]:
    potoken_extractor = PotokenExtractor(loop, update_interval=update_interval, browser_path=browser_path)
    token: TokenInfo = await potoken_extractor.run_once()
    return token
