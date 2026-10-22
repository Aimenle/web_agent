from pathlib import Path

import pytest

from aimenle.config import load_config

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://books.toscrape.com/catalogue/page-1.html"


@pytest.fixture
def site():
    return load_config(ROOT / "config" / "books.yaml")


@pytest.fixture
def listing_html():
    return (ROOT / "tests" / "fixtures" / "product_list.html").read_text(encoding="utf-8")


@pytest.fixture
def base_url():
    return BASE_URL
