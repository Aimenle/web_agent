from __future__ import annotations

import logging
import time
from typing import Dict, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests

log = logging.getLogger(__name__)

RETRY_STATUSES = {429, 500, 502, 503, 504}


class Fetcher:
    """HTTP client with per-host throttling, retries and robots.txt checks."""

    def __init__(self, user_agent, delay=1.5, timeout=15, retries=3, respect_robots=True):
        self.user_agent = user_agent
        self.delay = delay
        self.timeout = timeout
        self.retries = retries
        self.respect_robots = respect_robots

        self.session = requests.Session()
        self.session.headers["User-Agent"] = user_agent

        self._robots: Dict[str, RobotFileParser] = {}
        self._last_hit: Dict[str, float] = {}

    def _robots_for(self, url: str) -> RobotFileParser:
        parts = urlparse(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin in self._robots:
            return self._robots[origin]

        parser = RobotFileParser()
        try:
            resp = self.session.get(origin + "/robots.txt", timeout=self.timeout)
            if resp.status_code == 200:
                parser.parse(resp.text.splitlines())
            elif 400 <= resp.status_code < 500:
                # no robots.txt, nothing is restricted
                parser.allow_all = True
            else:
                parser.disallow_all = True
        except requests.RequestException as exc:
            log.warning("could not read robots.txt for %s: %s", origin, exc)
            parser.disallow_all = True

        self._robots[origin] = parser
        return parser

    def _throttle(self, url: str) -> None:
        host = urlparse(url).netloc
        last = self._last_hit.get(host)
        if last is not None:
            wait = self.delay - (time.monotonic() - last)
            if wait > 0:
                time.sleep(wait)

    def _mark(self, url: str) -> None:
        self._last_hit[urlparse(url).netloc] = time.monotonic()

    def get(self, url: str) -> Optional[bytes]:
        """Return the response body, or None if the page could not be fetched."""
        if self.respect_robots and not self._robots_for(url).can_fetch(self.user_agent, url):
            log.warning("skipping %s (disallowed by robots.txt)", url)
            return None

        for attempt in range(1, self.retries + 1):
            self._throttle(url)
            pause = 2 ** attempt
            try:
                resp = self.session.get(url, timeout=self.timeout)
            except requests.RequestException as exc:
                log.warning("request failed (%s), attempt %d/%d", exc, attempt, self.retries)
            else:
                if resp.status_code == 200:
                    self._mark(url)
                    return resp.content
                if resp.status_code not in RETRY_STATUSES:
                    log.warning("got HTTP %d for %s", resp.status_code, url)
                    self._mark(url)
                    return None
                retry_after = resp.headers.get("Retry-After", "")
                if retry_after.isdigit():
                    pause = min(int(retry_after), 60)
                log.warning("HTTP %d for %s, attempt %d/%d", resp.status_code, url, attempt, self.retries)
            self._mark(url)
            if attempt < self.retries:
                time.sleep(pause)

        return None
