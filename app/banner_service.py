"""Fetch the current Wuthering Waves banner into memory."""

from __future__ import annotations

import builtins
import json
import os
import time
from datetime import datetime, timezone
from typing import Any
from urllib.error import URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen


_print = builtins.print


def _debug_print(*args: object, **kwargs: object) -> None:
    if os.environ.get("TETHYS_DEBUG_BANNER") == "1":
        _print(*args, **kwargs)


print = _debug_print

DEFAULT_API_URL = (
    "https://gist.githubusercontent.com/yloove7/"
    "b1440f18d4c1152f9f3914fbdb2b7b14/raw/gistfile1.txt"
)
API_URL = os.environ.get("TETHYS_BANNER_API_URL", DEFAULT_API_URL)


def _request_bytes(url: str, cache_bust: bool = False, timeout: int = 8) -> bytes:
    if cache_bust:
        parts = urlsplit(url)
        query = dict(parse_qsl(parts.query))
        query["tethys_ts"] = str(int(time.time()))
        url = urlunsplit(parts._replace(query=urlencode(query)))
    
    print(f"[_request_bytes] Requisitando: {url}")
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Tethys v1.4"
                "AppleWebKit/537.36"
            ),
            "Accept": "application/json, image/avif, image/webp, image/*, */*",
            "Cache-Control": "no-cache",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # nosec B310
            data = response.read()
            print(f"[_request_bytes] [OK] Recebido {len(data)} bytes")
            return data
    except Exception as e:
        print(f"[_request_bytes] [ERROR] Erro: {e}")
        raise


def _as_list(payload: Any) -> list[dict[str, Any]]:
    print(f"[_as_list] Payload type: {type(payload)}")
    if isinstance(payload, list):
        print(f"[_as_list] Payload é list, retornando diretamente")
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        print(f"[_as_list] Payload não é dict, retornando vazio")
        return []
    
    print(f"[_as_list] Payload é dict com chaves: {list(payload.keys())}")
    for key in ("banners", "featured", "events", "data", "results"):
        nested = payload.get(key)
        print(f"[_as_list] Verificando chave '{key}': type={type(nested)}, is list={isinstance(nested, list)}")
        if isinstance(nested, list):
            result = [item for item in nested if isinstance(item, dict)]
            print(f"[_as_list] Encontrado '{key}' com {len(result)} itens")
            return result
    print(f"[_as_list] Nenhuma chave especial encontrada, retornando payload como lista única")
    return [payload]


def _first(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return value
    return None


def _parse_timestamp(value: Any) -> str | None:
    print(f"[_parse_timestamp] Parseando value: {value} (type: {type(value)})")
    
    if isinstance(value, (int, float)):
        timestamp = float(value)
        if timestamp > 10_000_000_000:
            timestamp /= 1000
        result = datetime.fromtimestamp(timestamp, timezone.utc).isoformat()
        print(f"[_parse_timestamp] Timestamp numeric: {result}")
        return result
    
    if not isinstance(value, str) or not value.strip():
        print(f"[_parse_timestamp] Value não é string válida")
        return None
    
    text = value.strip().replace("Z", "+00:00")
    print(f"[_parse_timestamp] Text após substituição: {text}")
    
    try:
        parsed = datetime.fromisoformat(text)
        print(f"[_parse_timestamp] Parsed datetime: {parsed}, tzinfo: {parsed.tzinfo}")
    except ValueError as e:
        print(f"[_parse_timestamp] [ERROR] Erro ao parsear: {e}")
        return None
    
    if parsed.tzinfo is None:
        print(f"[_parse_timestamp] Timezone era None, adicionando UTC")
        parsed = parsed.replace(tzinfo=timezone.utc)
    
    result = parsed.astimezone(timezone.utc).isoformat()
    print(f"[_parse_timestamp] [OK] Final result: {result}")
    return result


def _normalise_banner(item: dict[str, Any]) -> dict[str, Any] | None:
    print(f"[_normalise_banner] Item recebido: {item}")
    
    character = item.get("character")
    print(f"[_normalise_banner] character: {character}")
    
    if isinstance(character, dict):
        name = _first(character, "name", "title", "id")
        image_url = _first(character, "image", "imageUrl", "image_url", "icon")
        print(f"[_normalise_banner] Character é dict: name={name}, image_url={image_url}")
    else:
        name = character or _first(item, "name", "title", "characterName")
        image_url = None
        print(f"[_normalise_banner] Character não é dict, name={name}, image_url={image_url}")

    image_url = image_url or _first(
        item, "image", "imageUrl", "image_url", "bannerImage", "art"
    )
    print(f"[_normalise_banner] Final image_url: {image_url}")
    
    end_value = _first(
        item, "endTime", "end_time", "endDate", "end_date", "endsAt", "end"
    )
    print(f"[_normalise_banner] end_value: {end_value}")
    
    ends_at = _parse_timestamp(end_value)
    print(f"[_normalise_banner] ends_at parsed: {ends_at}")
    
    if not name or not image_url or not ends_at:
        print(f"[_normalise_banner] [ERROR] Falhando: name={not name}, image_url={not image_url}, ends_at={not ends_at}")
        return None
    
    result = {
        "name": str(name),
        "image_url": str(image_url),
        "ends_at": ends_at,
    }
    print(f"[_normalise_banner] [OK] Banner normalizado: {result}")
    return result


def _select_active(payload: Any) -> dict[str, Any] | None:
    candidates = _as_list(payload)
    print(f"[_select_active] Candidates: {len(candidates)} itens")
    
    now = datetime.now(timezone.utc)
    print(f"[_select_active] Hora atual (UTC): {now}")
    
    normalised: list[dict[str, Any]] = []
    for item in candidates:
        print(f"[_select_active] Processando item: {item}")
        banner = _normalise_banner(item)
        if banner is None:
            print(f"[_select_active] Banner não normalizado, pulando")
            continue
        try:
            end = datetime.fromisoformat(banner["ends_at"])
            print(f"[_select_active] End date: {end}, ativo? {end > now}")
        except ValueError as e:
            print(f"[_select_active] Erro ao parsear data: {e}")
            continue
        if end > now:
            print(f"[_select_active] [OK] Banner ativo: {banner['name']}")
            normalised.append(banner)
        else:
            print(f"[_select_active] [ERROR] Banner expirado: {banner['name']}")
    
    print(f"[_select_active] Total de banners ativos: {len(normalised)}")
    if not normalised:
        print(f"[_select_active] Nenhum banner ativo")
        return None
    
    result = min(normalised, key=lambda item: item["ends_at"])
    print(f"[_select_active] Banner selecionado (termina mais cedo): {result['name']}")
    return result


def fetch_current_banner() -> dict[str, Any] | None:
    """Fetch the active banner and keep its image bytes in memory only."""
    try:
        print("[Banner Service] Iniciando fetch...")
        payload = json.loads(
            _request_bytes(API_URL, timeout=6).decode("utf-8")
        )
        print(f"[Banner Service] Payload recebido: {type(payload)}")
        
        banner = _select_active(payload)
        print(f"[Banner Service] Banner selecionado: {banner}")
        
        if banner is None:
            raise ValueError("No active banner in API response")
        
        print(f"[Banner Service] Carregando imagem de: {banner.get('image_url')}")
        image_bytes = _request_bytes(banner["image_url"], timeout=8)
        print(f"[Banner Service] Imagem carregada: {len(image_bytes)} bytes")
        
        banner["image_bytes"] = image_bytes
        print(f"[Banner Service] Banner completo com imagem retornado")
        return banner
    except (OSError, URLError, ValueError, json.JSONDecodeError) as e:
        print(f"[Banner Service] [ERROR] Erro ao carregar banner: {e}")
        import traceback
        traceback.print_exc()
        return None
