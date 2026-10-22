from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import yaml

FIELD_TYPES = {"text", "price", "float", "int", "stars"}
DEFAULT_UA = "AimenleBot/0.1 (+https://github.com/your-name/aimenle)"


class ConfigError(ValueError):
    pass


@dataclass
class FieldSpec:
    name: str
    selector: Optional[str] = None
    attr: Optional[str] = None
    type: str = "text"


@dataclass
class SiteConfig:
    name: str
    start_urls: List[str]
    item_selector: str
    fields: List[FieldSpec]
    next_selector: Optional[str] = None
    delay: float = 1.5
    max_pages: int = 10
    user_agent: str = DEFAULT_UA
    respect_robots: bool = True


def load_config(path) -> SiteConfig:
    path = Path(path)
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML in {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ConfigError(f"{path} should contain a mapping at the top level")

    for key in ("name", "start_urls", "item_selector", "fields"):
        if key not in raw:
            raise ConfigError(f"missing required key '{key}' in {path}")

    if not raw["start_urls"]:
        raise ConfigError("start_urls cannot be empty")

    fields = []
    for fname, spec in (raw["fields"] or {}).items():
        spec = spec or {}
        ftype = spec.get("type", "text")
        if ftype not in FIELD_TYPES:
            raise ConfigError(
                f"field '{fname}' has unknown type '{ftype}' "
                f"(expected one of {sorted(FIELD_TYPES)})"
            )
        fields.append(
            FieldSpec(
                name=fname,
                selector=spec.get("selector"),
                attr=spec.get("attr"),
                type=ftype,
            )
        )

    if not any(f.name == "url" for f in fields):
        raise ConfigError("fields must include one called 'url'; it is used as the record key")

    return SiteConfig(
        name=raw["name"],
        start_urls=list(raw["start_urls"]),
        item_selector=raw["item_selector"],
        fields=fields,
        next_selector=raw.get("next_selector"),
        delay=float(raw.get("delay", 1.5)),
        max_pages=int(raw.get("max_pages", 10)),
        user_agent=raw.get("user_agent", DEFAULT_UA),
        respect_robots=bool(raw.get("respect_robots", True)),
    )
