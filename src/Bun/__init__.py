"""Bun TUI package."""

import logging

for _logger_name in ("textual_image", "textual_image._terminal"):
    logger = logging.getLogger(_logger_name)
    logger.setLevel(logging.CRITICAL)
    logger.propagate = False
    logger.disabled = True
