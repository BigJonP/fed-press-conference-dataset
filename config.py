"""
Configuration file for the FED Press Conference Scraper

This file contains all configurable parameters for the scraper.
"""

from dataclasses import dataclass


@dataclass
class ScraperConfig:
    """Configuration class for the scraper"""

    base_url: str = "https://www.federalreserve.gov/mediacenter/files/"

    output_dir: str = "fed_press_conferences"

    request_timeout: int = 30

    delay: float = 1.0

    max_retries: int = 3
    retry_delay: float = 2.0

    log_level: str = "INFO"
    log_file: str = "scraper.log"

    user_agent: str = (
        "FED-Press-Conference-Scraper/1.0 (+https://github.com/<yourusername>/fed-scraper)"
    )


DEFAULT_CONFIG = ScraperConfig()
