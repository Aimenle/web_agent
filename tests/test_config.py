import pytest

from aimenle.config import ConfigError, load_config


def test_example_config_loads(site):
    assert site.name == "books_toscrape"
    assert {f.name for f in site.fields} >= {"title", "url", "price"}


def test_missing_key_is_reported(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("name: x\nstart_urls: [http://a.test]\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="item_selector"):
        load_config(path)


def test_unknown_field_type(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        "name: x\nstart_urls: [http://a.test]\nitem_selector: div\n"
        "fields:\n  url:\n    selector: a\n    attr: href\n  p:\n    type: money\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="unknown type"):
        load_config(path)


def test_url_field_is_required(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        "name: x\nstart_urls: [http://a.test]\nitem_selector: div\nfields:\n  title:\n    selector: h1\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="url"):
        load_config(path)
