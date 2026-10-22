# Aimenle

Aimenle is a small, config-driven scraper for product listings. You describe a
site once in a YAML file (where the items are, which fields to pull, how to
find the next page) and the bot crawls it, stores the results in SQLite and can
export them to CSV or JSON.

It is meant as a starting point: the core is a few hundred lines with no
framework, so it is easy to read and change.

## Features

- Site definitions in YAML, no code needed for simple listing pages
- Pagination following with a page limit
- Per-host rate limiting, retries with backoff, `Retry-After` support
- `robots.txt` is checked before every request (can be switched off per site)
- Results go into SQLite, re-running updates existing rows instead of duplicating them
- Export to CSV or JSON
- Typed fields: text, price, int, float, star ratings

## Install

Requires Python 3.9 or newer.

```bash
git clone https://github.com/aimenle/web_agent.git
cd aimenle
python -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -e .
```

## Usage

Run the bundled example (it targets books.toscrape.com, a practice site):

```bash
aimenle run config/books.yaml
```

Options:

```bash
aimenle run config/books.yaml --max-pages 2 --delay 2
aimenle run config/books.yaml --db data/books.db
```

Export what was collected:

```bash
aimenle export out/books.csv
aimenle export out/books.json --source books_toscrape
```

You can also run it without installing: `python -m aimenle run config/books.yaml`.

## Writing a site config

```yaml
name: my_shop                    # used as the source label in the database
start_urls:
  - https://shop.example/products?page=1

delay: 1.5                       # seconds between requests to the same host
max_pages: 10
respect_robots: true
user_agent: "AimenleBot/0.1 (+https://github.com/your-name/aimenle)"

item_selector: "div.product"     # one element per product
next_selector: "a.next"          # optional, link to the next page

fields:
  title:
    selector: "h2.name"
  url:                           # required, it identifies a product
    selector: "a"
    attr: href
  price:
    selector: ".price"
    type: price
```

Each field has:

| key        | meaning                                                              |
|------------|----------------------------------------------------------------------|
| `selector` | CSS selector, relative to the item. Leave out to use the item itself |
| `attr`     | Read an attribute instead of the text (`href`, `src`, `title`, ...)  |
| `type`     | `text` (default), `price`, `float`, `int` or `stars`                 |

Links in `href` and `src` are turned into absolute URLs. A field called `url`
is mandatory; items without one are skipped.

## Project layout

```
aimenle/
  cli.py        command line entry point
  bot.py        crawl loop (queue, pagination, page limit)
  fetcher.py    HTTP, throttling, retries, robots.txt
  parser.py     HTML to dicts, driven by the config
  storage.py    SQLite storage and exports
  config.py     YAML loading and validation
config/         example site configs
tests/          unit tests and an HTML fixture
```

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The tests run offline: the crawl loop is tested with a fake fetcher and the
parser with a saved HTML fixture.

## Scraping responsibly

Check a site's terms of service and `robots.txt` before scraping it, keep the
delay reasonable, and identify your bot with a real contact URL in the
`user_agent`. Do not use this against sites that forbid automated access, and be
careful with personal data. You are responsible for how you use the tool.

## Limitations

- Pages are fetched with plain HTTP, so content rendered by JavaScript is not
  visible. For those sites you would need to add a browser backend such as
  Playwright to `fetcher.py`.
- Only listing pages are parsed. Following links into detail pages is a
  natural next step.

## License


