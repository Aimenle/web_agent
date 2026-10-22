from aimenle.parser import next_page_url, parse_items


def test_parses_all_linked_items(site, listing_html, base_url):
    items = parse_items(listing_html, base_url, site)
    # the third card has no link, so it is dropped
    assert len(items) == 2


def test_fields_are_extracted_and_typed(site, listing_html, base_url):
    first = parse_items(listing_html, base_url, site)[0]
    assert first["title"] == "A Light in the Attic"
    assert first["price"] == 51.77
    assert first["rating"] == 3
    assert first["availability"] == "In stock"


def test_urls_are_made_absolute(site, listing_html, base_url):
    first = parse_items(listing_html, base_url, site)[0]
    assert first["url"] == "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"


def test_price_with_thousands_separator(site, listing_html, base_url):
    second = parse_items(listing_html, base_url, site)[1]
    assert second["price"] == 1053.74


def test_next_page_url(site, listing_html, base_url):
    assert next_page_url(listing_html, base_url, site) == "https://books.toscrape.com/catalogue/page-2.html"


def test_no_next_page(site, base_url):
    html = "<html><body><article class='product_pod'></article></body></html>"
    assert next_page_url(html, base_url, site) is None
