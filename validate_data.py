#!/usr/bin/env python3
"""Validate character data consistency across all catalogs."""

from src.wuwa_calculator.data.characters_ids import KNOWN_CHARACTER_IDS
from src.data.characters_elements import CHARACTER_ELEMENTS
from src.data.characters_quotes import CHARACTER_QUOTES
from src.wuwa_calculator.data.images import CHARACTER_IMAGE_FALLBACKS
from src.wuwa_calculator.data.characters_urls import RACKOON_CHARACTER_SLUGS
from src.wuwa_calculator.data.weapons import _LOCAL_KIT_WEAPON_NAMES

ids_set = KNOWN_CHARACTER_IDS
els_set = set(CHARACTER_ELEMENTS.keys())
qts_set = set(CHARACTER_QUOTES.keys())
imgs_set = set(CHARACTER_IMAGE_FALLBACKS.keys())
urls_set = set(RACKOON_CHARACTER_SLUGS.keys())
wpns_set = set(_LOCAL_KIT_WEAPON_NAMES.keys())

print("=== VALIDAÇÃO DE INTEGRIDADE ===")
print(f"Total de personagens: {len(ids_set)}")
print(f"\nElements: {len(els_set)} - Faltando: {sorted(ids_set - els_set) if ids_set - els_set else '✓ NENHUM'}")
print(f"Quotes: {len(qts_set)} - Faltando: {sorted(ids_set - qts_set) if ids_set - qts_set else '✓ NENHUM'}")
print(f"Images: {len(imgs_set)} - Faltando: {sorted(ids_set - imgs_set) if ids_set - imgs_set else '✓ NENHUM'}")
print(f"URLs: {len(urls_set)} - Faltando: {sorted(ids_set - urls_set) if ids_set - urls_set else '✓ NENHUM'}")
print(f"Weapons: {len(wpns_set)} - Faltando: {sorted(ids_set - wpns_set) if ids_set - wpns_set else '✓ NENHUM'}")

if not (ids_set - els_set or ids_set - qts_set or ids_set - imgs_set or ids_set - urls_set or ids_set - wpns_set):
    print("\n✓ ✓ ✓ TODOS OS DADOS CARREGADOS COM SUCESSO ✓ ✓ ✓")
else:
    print("\n✗ Há inconsistências nos dados!")
