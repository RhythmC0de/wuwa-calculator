"""Integração com WuwaTracker para dados de banners atualizados - Multi-source strategy."""

import builtins
import json
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Any
from urllib.parse import urljoin
from urllib.request import Request, urlopen


_print = builtins.print


def _debug_print(*args: object, **kwargs: object) -> None:
    if os.environ.get("TETHYS_DEBUG_BANNER") == "1":
        _print(*args, **kwargs)


print = _debug_print


def fetch_current_banner_cascading() -> dict[str, Any] | None:
    """
    Estratégia de cascata: tenta WuwaTracker → Gist → Jingyuan padrão.
    Retorna um dicionário com:
    {
        'name': str (nome do personagem),
        'image_bytes': bytes (imagem já baixada),
        'ends_at': str (data de término em ISO format),
        'source': str ('wuwatracker', 'gist', ou 'fallback')
    }
    """
    print("[Banner Cascade] Iniciando estratégia de cascata de fontes...")
    
    # Passo 1: Tenta WuwaTracker
    print("\n[Banner Cascade] 1️⃣ Tentando WuwaTracker...")
    banner = _try_wuwatracker()
    if banner:
        print(f"[Banner Cascade] ✅ Sucesso: WuwaTracker ({banner.get('name')})")
        return banner
    
    # Passo 2: Tenta Gist (fallback confiável)
    print("\n[Banner Cascade] 2️⃣ Tentando Gist (fallback confiável)...")
    banner = _try_gist()
    if banner:
        print(f"[Banner Cascade] ✅ Sucesso: Gist ({banner.get('name')})")
        return banner
    
    # Passo 3: Carrega Jingyuan padrão (último resort)
    print("\n[Banner Cascade] 3️⃣ Carregando Jingyuan padrão (último resort)...")
    banner = _try_jingyuan_fallback()
    if banner:
        print(f"[Banner Cascade] ✅ Sucesso: Jingyuan padrão")
        return banner
    
    print("[Banner Cascade] ❌ Todas as fontes falharam!")
    return None


def _try_wuwatracker() -> dict[str, Any] | None:
    """Tenta WuwaTracker - endpoints experimentais."""
    urls_to_try = [
        "https://wuwatracker.com/api/banners",
        "https://api.wuwatracker.com/banners",
        "https://wuwatracker.com/api/v1/banners",
    ]
    
    for url in urls_to_try:
        try:
            print(f"  [WuwaTracker] GET {url}...")
            request = Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Accept": "application/json",
                },
            )
            with urlopen(request, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                print(f"  [WuwaTracker] ✓ API respondeu com sucesso!")
                
                banner = _parse_tracker_response(data)
                if banner and banner.get("image_url"):
                    # Download a imagem
                    try:
                        image_bytes = _download_image(banner["image_url"])
                        banner["image_bytes"] = image_bytes
                        banner["source"] = "wuwatracker"
                        return banner
                    except Exception as e:
                        print(f"  [WuwaTracker] ✗ Erro ao baixar imagem: {e}")
                        continue
        except Exception as e:
            print(f"  [WuwaTracker] ✗ {url} falhou: {type(e).__name__}")
            continue
    
    return None


def _try_gist() -> dict[str, Any] | None:
    """Tenta Gist - fallback confiável com URL de imagem pronta."""
    try:
        print(f"  [Gist] Requisitando banner_service...")
        from src.wuwa_calculator.app.banner_service import fetch_current_banner
        banner = fetch_current_banner()
        if banner:
            banner["source"] = "gist"
            print(f"  [Gist] ✓ Banner carregado com sucesso")
            return banner
        else:
            print(f"  [Gist] ✗ banner_service retornou None")
            return None
    except Exception as e:
        print(f"  [Gist] ✗ Erro: {type(e).__name__}: {e}")
        return None


def _try_jingyuan_fallback() -> dict[str, Any] | None:
    """Carrega Jingyuan padrão como último resort."""
    try:
        print(f"  [Jingyuan] Carregando imagem padrão...")
        image_bytes = _download_image("https://i.imgur.com/JrRW9Bt.jpeg")
        ends_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        
        return {
            "name": "Jingyuan",
            "image_bytes": image_bytes,
            "ends_at": ends_at,
            "source": "fallback",
        }
    except Exception as e:
        print(f"  [Jingyuan] ✗ Erro: {type(e).__name__}: {e}")
        return None


def _download_image(url: str) -> bytes:
    """Download de imagem com timeout e headers apropriados."""
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
    )
    with urlopen(request, timeout=10) as response:
        return response.read()


def _parse_tracker_response(data: dict[str, Any]) -> dict[str, Any] | None:
    """Parse da resposta do WuwaTracker em formato conhecido."""
    try:
        if isinstance(data, dict):
            banners = data.get("banners", data.get("data", []))
            
            if isinstance(banners, list) and len(banners) > 0:
                current_banner = banners[0]
                
                return {
                    "name": current_banner.get("name", "Unknown"),
                    "image_url": current_banner.get("image", current_banner.get("image_url", "")),
                    "ends_at": current_banner.get("endDate", current_banner.get("ends_at", "")),
                    "rarity": current_banner.get("rarity", 5),
                    "element": current_banner.get("element", ""),
                }
        
        return None
    except Exception as e:
        print(f"  [Parser] ✗ Erro ao parsear: {type(e).__name__}")
        return None


def fetch_banner_catalog() -> list[dict[str, Any]]:
    """Reads the public banner-history page used by WuwaTracker."""
    page_url = "https://wuwatracker.com/pt/banner-history"
    try:
        request = Request(
            page_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml",
            },
        )
        with urlopen(request, timeout=12) as response:
            html = response.read().decode("utf-8", errors="replace")
    except Exception as exc:
        print(f"[WuwaTracker page] {type(exc).__name__}: {exc}")
        return []

    normalized_html = html.replace('\\"', '"')
    pattern = re.compile(
        r'"character":\{"name":"(?P<name>[^"]+)",'
        r'"iconSrc":"(?P<icon>[^"]+)".*?'
        r'"firstStartDate":"(?P<start>[^"]+)"',
    )
    catalog: list[dict[str, Any]] = []
    seen: set[str] = set()
    for match in pattern.finditer(normalized_html):
        name = match.group("name")
        start = match.group("start")
        icon_path = match.group("icon")
        if name == "next-size-adjust" or "/api/character-icons/" not in icon_path:
            continue
        if name in seen:
            continue
        seen.add(name)
        image_url = urljoin(page_url, icon_path)
        if name.casefold() == "qingxiao":
            image_url = "https://i.imgur.com/lq6O5Vo.jpeg"
        # The page publishes the start date; the 14-day phase window keeps
        # the current announced phase visible without inventing API data.
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        catalog.append({
            "name": name,
            "image_url": image_url,
            "image_bytes": b"",
            "starts_at": start_date.isoformat(),
            "ends_at": (start_date + timedelta(days=14)).isoformat(),
            "rarity": 5,
            "speculated": False,
            "source": "wuwatracker-page",
        })
    catalog.sort(key=lambda item: str(item.get("starts_at", "")))
    for index, item in enumerate(catalog):
        if index + 1 < len(catalog):
            item["ends_at"] = catalog[index + 1]["starts_at"]

    now = datetime.now(timezone.utc)
    current_index = next(
        (
            index for index, item in enumerate(catalog)
            if item["starts_at"] <= now.isoformat() <= item["ends_at"]
        ),
        len(catalog) - 1,
    )
    selected_indices = set(range(max(0, current_index - 1), min(len(catalog), current_index + 3)))
    selected = [item for index, item in enumerate(catalog) if index in selected_indices]
    for item in selected:
        try:
            item["image_bytes"] = _download_image(str(item["image_url"]))
        except Exception as exc:
            print(f"[WuwaTracker page] imagem de {item['name']} indisponível: {type(exc).__name__}")
    return selected


def fetch_current_banner_from_tracker() -> dict[str, Any] | None:
    """
    Compatibilidade com código anterior.
    Chama a estratégia de cascata.
    """
    return fetch_current_banner_cascading()


def get_banner_from_tracker_or_fallback(fallback_banner_data: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """
    Compatibilidade com código anterior.
    Tenta cascata e usa fallback se ambos falharem.
    """
    banner = fetch_current_banner_cascading()
    
    if banner:
        print(f"[Cascade] Usando banner de {banner.get('source', 'unknown')}")
        return banner
    
    if fallback_banner_data:
        print("[Cascade] Usando banner fallback fornecido")
        return fallback_banner_data
    
    print("[Cascade] Nenhum banner disponível!")
    return None
