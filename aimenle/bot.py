from __future__ import annotations

import logging
from collections import deque

from aimenle.config import SiteConfig
from aimenle.fetcher import Fetcher
from aimenle.parser import next_page_url, parse_items
from aimenle.storage import Store

log = logging.getLogger(__name__)


class Bot:
    """Walks a site starting from its start URLs and stores what it finds."""

    def __init__(self, site: SiteConfig, fetcher: Fetcher, store: Store):
        self.site = site
        self.fetcher = fetcher
        self.store = store

    def run(self) -> int:
        queue = deque(self.site.start_urls)
        seen = set()
        pages = 0
        stored = 0

        while queue and pages < self.site.max_pages:
            url = queue.popleft()
            if url in seen:
                continue
            seen.add(url)

            html = self.fetcher.get(url)
            if html is None:
                continue
            pages += 1

            items = parse_items(html, url, self.site)
            stored += self.store.save(self.site.name, items)
            log.info("page %d: %d items from %s", pages, len(items), url)

            following = next_page_url(html, url, self.site)
            if following and following not in seen:
                queue.append(following)

        log.info("finished: %d pages, %d items stored", pages, stored)
        return stored
