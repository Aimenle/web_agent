from aimenle.bot import Bot
from aimenle.storage import Store


class FakeFetcher:
    """Serves canned pages so the crawl loop can be tested offline."""

    def __init__(self, pages):
        self.pages = pages
        self.requested = []

    def get(self, url):
        self.requested.append(url)
        return self.pages.get(url)


def test_follows_pagination_until_it_ends(site, listing_html):
    first = site.start_urls[0]
    second = "https://books.toscrape.com/catalogue/page-2.html"
    last_page = "<html><body></body></html>"

    fetcher = FakeFetcher({first: listing_html, second: last_page})
    store = Store(":memory:")

    stored = Bot(site, fetcher, store).run()

    assert fetcher.requested == [first, second]
    assert stored == 2
    assert store.count(site.name) == 2


def test_respects_max_pages(site, listing_html):
    site.max_pages = 1
    fetcher = FakeFetcher({site.start_urls[0]: listing_html})
    Bot(site, fetcher, Store(":memory:")).run()
    assert len(fetcher.requested) == 1


def test_failed_page_is_skipped(site):
    fetcher = FakeFetcher({})
    store = Store(":memory:")
    assert Bot(site, fetcher, store).run() == 0
