import json

from aimenle.storage import Store


def make_item(url, price):
    return {"url": url, "title": "Item", "price": price}


def test_save_and_count():
    store = Store(":memory:")
    store.save("shop", [make_item("https://x.test/1", 10.0), make_item("https://x.test/2", 12.5)])
    assert store.count() == 2
    assert store.count("shop") == 2
    assert store.count("other") == 0


def test_same_url_is_updated_not_duplicated():
    store = Store(":memory:")
    store.save("shop", [make_item("https://x.test/1", 10.0)])
    store.save("shop", [make_item("https://x.test/1", 8.0)])
    rows = store.rows("shop")
    assert len(rows) == 1
    assert rows[0]["price"] == 8.0


def test_export_json_and_csv(tmp_path):
    store = Store(":memory:")
    store.save("shop", [make_item("https://x.test/1", 10.0)])

    json_path = tmp_path / "out.json"
    assert store.export(json_path, "json") == 1
    assert json.loads(json_path.read_text(encoding="utf-8"))[0]["url"] == "https://x.test/1"

    csv_path = tmp_path / "out.csv"
    assert store.export(csv_path, "csv") == 1
    header = csv_path.read_text(encoding="utf-8").splitlines()[0]
    assert "url" in header and "price" in header
