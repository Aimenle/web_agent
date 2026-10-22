from __future__ import annotations

import re
from typing import Dict, List, Optional, Union
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from aimenle.config import FieldSpec, SiteConfig

NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
STAR_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
URL_ATTRS = {"href", "src"}


def _convert(value: str, kind: str):
    if kind == "text":
        return value
    if kind in ("price", "float"):
        match = NUMBER_RE.search(value.replace(",", ""))
        return float(match.group()) if match else None
    if kind == "int":
        match = re.search(r"\d+", value.replace(",", ""))
        return int(match.group()) if match else None
    if kind == "stars":
        for word in value.lower().split():
            if word in STAR_WORDS:
                return STAR_WORDS[word]
        return None
    raise ValueError(f"unknown field type: {kind}")


def _extract(node, spec: FieldSpec, base_url: str):
    target = node.select_one(spec.selector) if spec.selector else node
    if target is None:
        return None

    if spec.attr:
        value = target.get(spec.attr)
        if value is None:
            return None
        if isinstance(value, list):  # class and rel come back as lists
            value = " ".join(value)
        if spec.attr in URL_ATTRS:
            value = urljoin(base_url, value)
    else:
        value = " ".join(target.get_text(" ").split())

    return _convert(value, spec.type)


def _soup(html: Union[str, bytes]) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


def parse_items(html: Union[str, bytes], base_url: str, site: SiteConfig) -> List[Dict]:
    soup = _soup(html)
    items = []
    for node in soup.select(site.item_selector):
        row = {f.name: _extract(node, f, base_url) for f in site.fields}
        if not row.get("url"):
            continue
        items.append(row)
    return items


def next_page_url(html: Union[str, bytes], base_url: str, site: SiteConfig) -> Optional[str]:
    if not site.next_selector:
        return None
    link = _soup(html).select_one(site.next_selector)
    if link is None or not link.get("href"):
        return None
    return urljoin(base_url, link["href"])
