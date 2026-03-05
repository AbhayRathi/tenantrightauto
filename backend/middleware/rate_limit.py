import logging
from slowapi import Limiter  # type: ignore[import]
from slowapi.util import get_remote_address  # type: ignore[import]
import os

logger = logging.getLogger(__name__)

RATE_LIMIT = os.environ.get("RATE_LIMIT_PER_MINUTE", "20")

limiter = Limiter(key_func=get_remote_address, default_limits=[f"{RATE_LIMIT}/minute"])
