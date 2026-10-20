"""Catálogo de personagens: lê os JSON de ``data/characters`` no idioma pedido.

Único ponto do aplicativo que sabe onde ficam os arquivos e como o texto é
traduzido. A interface só faz::

    from wuwa_calculator.infrastructure import catalog
    ficha = catalog.character("luuk herssen", "PT-BR")
    ficha.skills[0].name

Estrutura em disco (``data/characters``)::

    data/<id>/<id>.json        ficha do personagem
    skills/<pasta>/<hab>.json  uma habilidade (referenciada pela ficha)

Texto traduzível = dicionário cujas chaves são só idiomas::

    "name": {"pt-BR": "Ataque Básico", "en": "Basic Attack"}

Qualquer campo pode ser traduzido assim (inclusive dentro de listas). Texto
simples (string) vale para todos os idiomas. Idioma ausente usa o inglês, depois
o português; sem nenhum, vazio.

Campos reconhecidos na ficha (todos opcionais)::

    id, name, rarity, element, weapon_type, quotes[], base_stats{},
    weapon{name, passive}, images{character, weapon},
    team_buffs[{name, value}], personal_buffs[{name, value}], skills{}

``base_stats`` aceita as chaves atk, hp, def, crit_rate, crit_dmg, max_energy.
Imagens: URL https permitida ou caminho relativo a ``data/``.

Enquanto o JSON de um campo estiver vazio, o catálogo usa os dados antigos de
``data/*.py`` (fallback de transição). Quando o JSON estiver completo, apague
esses arquivos: o fallback some sozinho.
"""

from __future__ import annotations

import importlib
import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

_LOG = logging.getLogger(__name__)

LANGUAGES = ("pt-br", "en")
FALLBACK_CHAIN = ("en", "pt-br")
MAX_FILE_BYTES = 512 * 1024
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

SKILL_ORDER = (
    "basic_attack",
    "resonance_skill",
    "forte_circuit",
    "resonance_liberation",
    "intro_skill",
    "outro_skill",
)
SKILL_LABELS = {
    "basic_attack": {"pt-BR": "Ataque Básico", "en": "Basic Attack"},
    "resonance_skill": {"pt-BR": "Habilidade de Ressonância", "en": "Resonance Skill"},
    "forte_circuit": {"pt-BR": "Circuito Forte", "en": "Forte Circuit"},
    "resonance_liberation": {"pt-BR": "Liberação de Ressonância", "en": "Resonance Liberation"},
    "intro_skill": {"pt-BR": "Habilidade de Entrada", "en": "Intro Skill"},
    "outro_skill": {"pt-BR": "Habilidade de Saída", "en": "Outro Skill"},
}
ELEMENTS = ("Aero", "Glacio", "Electro", "Fusion", "Havoc", "Spectro")
_VARIANT_ALIASES = {"electro": ("electro", "eletro")}
_STAT_LABELS = {
    "hp": "Base HP", "atk": "Base ATK", "def": "Base DEF",
    "crit_rate": "Crit Rate", "crit_dmg": "Crit DMG", "max_energy": "Max Energy",
}
_PERCENT_STATS = {"crit_rate", "crit_dmg"}
_PART = re.compile(r"^[a-z0-9_]+$")


# --------------------------------------------------------------------- idioma
def normalize_language(code: str) -> str:
    return (code or "").strip().casefold().replace("_", "-")


def is_localized(value: Any) -> bool:
    """Dicionário não vazio cujas chaves são todas idiomas conhecidos."""
    return (
        isinstance(value, dict)
        and bool(value)
        and all(normalize_language(key) in LANGUAGES for key in value)
    )


def pick_text(value: dict, language: str) -> str:
    by_language = {normalize_language(key): text for key, text in value.items()}
    for code in (normalize_language(language), *FALLBACK_CHAIN):
        text = by_language.get(code)
        if isinstance(text, str) and text.strip():
            return text
    return ""


def resolve(value: Any, language: str) -> Any:
    """Troca cada texto traduzível pelo texto do idioma, em qualquer nível."""
    if is_localized(value):
        return pick_text(value, language)
    if isinstance(value, dict):
        return {key: resolve(item, language) for key, item in value.items()}
    if isinstance(value, list):
        return [resolve(item, language) for item in value]
    return value


# ------------------------------------------------------------------------ ids
def slug(character_id: str) -> str:
    """'luuk herssen' (id do app) -> 'luuk_herssen' (pasta). Rejeita o resto."""
    value = (character_id or "").strip().casefold().replace(" ", "_")
    if not _PART.fullmatch(value):
        raise ValueError(f"id inválido: {character_id!r}")
    return value


def split_variant(character_id: str) -> tuple[str, str]:
    """'rover aero' -> ('rover', 'aero'). Os demais ids não têm variante."""
    cid = (character_id or "").strip().casefold()
    if cid.startswith("rover "):
        return "rover", cid.split(" ", 1)[1].strip()
    return cid, ""


def _safe_ref(ref: str) -> str | None:
    parts = str(ref).strip("/").split("/")
    return "/".join(parts) if parts and all(_PART.fullmatch(p) for p in parts) else None


# ------------------------------------------------------------------- modelos
@dataclass(frozen=True)
class Skill:
    key: str
    name: str
    description: str


@dataclass(frozen=True)
class Weapon:
    name: str = ""
    passive: str = ""


@dataclass(frozen=True)
class Character:
    id: str
    name: str
    element: str = ""
    rarity: int | None = None
    weapon_type: str = ""
    quotes: tuple[str, ...] = ()
    stats: dict[str, str] = field(default_factory=dict)
    weapon: Weapon = Weapon()
    image_character: str = ""
    image_weapon: str = ""
    skills: tuple[Skill, ...] = ()
    team_buffs: tuple[tuple[str, float], ...] = ()
    personal_buffs: tuple[tuple[str, float], ...] = ()

    @property
    def has_data(self) -> bool:
        return bool(self.skills or self.quotes or self.stats or self.weapon.name)


@dataclass
class IntegrityReport:
    errors: list[str]
    warnings: list[str]


# -------------------------------------------------------------- dados antigos
class LegacyData:
    """Dados dos antigos ``data/*.py``. Some sozinho quando os arquivos saem."""

    _MODULES = (
        "characters_elements", "characters_kits", "characters_quotes",
        "characters_stats", "images", "weapons", "characters_ids",
    )

    def __init__(self) -> None:
        self._loaded: dict[str, Any] = {}
        package = (__package__ or "wuwa_calculator.infrastructure").rsplit(".", 1)[0]
        self._package = f"{package}.data"

    def _module(self, name: str) -> Any:
        if name not in self._loaded:
            try:
                self._loaded[name] = importlib.import_module(f"{self._package}.{name}")
            except ImportError as error:
                _LOG.debug("catálogo: dados antigos %s indisponíveis (%s)", name, error)
                self._loaded[name] = None
        return self._loaded[name]

    def _get(self, module: str, attribute: str, default: Any) -> Any:
        loaded = self._module(module)
        return getattr(loaded, attribute, default) if loaded else default

    def known_ids(self) -> set[str]:
        return set(self._get("characters_ids", "KNOWN_CHARACTER_IDS", set()))

    def element(self, cid: str) -> str:
        return str(self._get("characters_elements", "CHARACTER_ELEMENTS", {}).get(cid, ""))

    def quotes(self, cid: str) -> tuple[str, ...]:
        return tuple(self._get("characters_quotes", "CHARACTER_QUOTES", {}).get(cid, ()))

    def stats(self, cid: str) -> dict[str, str]:
        return dict(self._get("characters_stats", "CHARACTER_STATS_DB", {}).get(cid, {}))

    def images(self, cid: str) -> dict[str, str]:
        return dict(self._get("images", "CHARACTER_IMAGE_FALLBACKS", {}).get(cid, {}))

    def kit(self, cid: str) -> dict[str, Any]:
        db = self._get("characters_kits", "CHARACTER_KITS_DB", {})
        manual = self._get("characters_kits", "MANUAL_CHARACTER_KITS", {})
        return db.get(cid) or manual.get(cid) or {}

    def weapon_name(self, cid: str) -> str:
        local = self._get("weapons", "_LOCAL_KIT_WEAPON_NAMES", {})
        return str(local.get(cid) or self.kit(cid).get("weapon_name", ""))

    def manual_weapon(self, cid: str) -> dict[str, Any]:
        return self._get("weapons", "MANUAL_WEAPONS", {}).get(cid, {})


class NoLegacy(LegacyData):
    """Sem dados antigos (testes e, no futuro, o estado final)."""

    def __init__(self) -> None:
        self._loaded = {}

    def _get(self, module: str, attribute: str, default: Any) -> Any:
        return default


# -------------------------------------------------------------------- catálogo
class Catalog:
    def __init__(self, data_dir: Path | None = None, legacy: LegacyData | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir is not None else DATA_DIR
        self.legacy = legacy if legacy is not None else LegacyData()
        self._cache: dict[str, Any] = {}

    def clear_cache(self) -> None:
        self._cache.clear()

    # ------------------------------------------------------------- leitura
    def _read(self, relative: str) -> Any:
        """JSON ou None (ausente, vazio, grande demais, quebrado ou fora de data/)."""
        if relative in self._cache:
            return self._cache[relative]
        data: Any = None
        root = self.data_dir.resolve()
        path = (root / relative).resolve()
        if root in path.parents and path.is_file():
            try:
                if 0 < path.stat().st_size <= MAX_FILE_BYTES:
                    data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as error:
                _LOG.warning("catálogo: não consegui ler %s (%s)", relative, error)
        self._cache[relative] = data
        return data

    def _skill_files(self, base: str, variant: str, sheet: dict[str, Any]) -> dict[str, dict]:
        refs: dict[str, Any] = dict(sheet.get("skills") or {})
        variant_def = (sheet.get("variants") or {}).get(variant) if variant else None
        if isinstance(variant_def, dict) and variant_def.get("skills"):
            refs = dict(variant_def["skills"])

        keys = list(SKILL_ORDER) + [key for key in refs if key not in SKILL_ORDER]
        found: dict[str, dict] = {}
        for key in keys:
            candidates: list[str] = []
            if refs.get(key):
                candidates.append(str(refs[key]))
            if variant:
                for name in _VARIANT_ALIASES.get(variant, (variant,)):
                    candidates.append(f"{base}/{name}/{key}")
            else:
                candidates.append(f"{base}/{key}")
            for candidate in candidates:
                safe = _safe_ref(candidate)
                data = self._read(f"characters/skills/{safe}.json") if safe else None
                if isinstance(data, dict):
                    found[key] = data
                    break
        return found

    def raw_character(self, character_id: str) -> tuple[dict[str, Any], dict[str, dict]]:
        """(ficha, habilidades) sem traduzir. Vazios se o personagem não tem JSON."""
        base, variant = split_variant(character_id)
        name = slug(base)
        sheet = self._read(f"characters/data/{name}/{name}.json")
        sheet = sheet if isinstance(sheet, dict) else {}
        return sheet, self._skill_files(name, variant, sheet)

    # -------------------------------------------------------------- ficha
    def character(self, character_id: str, language: str = "PT-BR") -> Character:
        cid = (character_id or "").strip().casefold()
        _base, variant = split_variant(cid)
        raw_sheet, raw_skills = self.raw_character(cid)
        sheet = resolve(raw_sheet, language)
        legacy = self.legacy
        kit = legacy.kit(cid)

        element = self._element(variant or sheet.get("element") or legacy.element(cid))
        weapon_json = sheet.get("weapon") if isinstance(sheet.get("weapon"), dict) else {}
        manual = legacy.manual_weapon(cid)
        manual_text = resolve({k: v for k, v in manual.items() if k in ("PT-BR", "EN")}, language)

        weapon = Weapon(
            name=str(
                weapon_json.get("name") or manual.get("name")
                or legacy.weapon_name(cid) or ""
            ),
            passive=str(
                weapon_json.get("passive") or manual_text
                or kit.get("weapon_passive", "") or ""
            ),
        )
        images = sheet.get("images") if isinstance(sheet.get("images"), dict) else {}
        old_images = legacy.images(cid)

        return Character(
            id=cid,
            name=str(sheet.get("name") or cid.title()),
            element=element,
            rarity=sheet.get("rarity") if isinstance(sheet.get("rarity"), int) else None,
            weapon_type=str(sheet.get("weapon_type") or ""),
            quotes=self._quotes(sheet.get("quotes")) or legacy.quotes(cid),
            stats=self._stats(sheet.get("base_stats")) or legacy.stats(cid),
            weapon=weapon,
            image_character=self._image(images.get("character")) or str(old_images.get("char", "")),
            image_weapon=self._image(images.get("weapon")) or str(old_images.get("weapon", "")),
            skills=self._skills(raw_skills, language) or self._legacy_skills(kit),
            team_buffs=self._buffs(sheet.get("team_buffs")) or self._buffs(kit.get("team_buffs")),
            personal_buffs=self._buffs(sheet.get("personal_buffs"))
            or self._buffs(kit.get("personal_buffs")),
        )

    # ------------------------------------------------------ conversões
    @staticmethod
    def _element(value: Any) -> str:
        text = str(value or "").strip().casefold()
        return next((name for name in ELEMENTS if name.casefold() == text), "")

    @staticmethod
    def _quotes(value: Any) -> tuple[str, ...]:
        return tuple(str(item) for item in value or [] if isinstance(item, str) and item.strip())

    @staticmethod
    def _stats(value: Any) -> dict[str, str]:
        if not isinstance(value, dict):
            return {}
        result: dict[str, str] = {}
        for key, number in value.items():
            if number in (None, ""):
                continue
            label = _STAT_LABELS.get(str(key), str(key))
            if isinstance(number, (int, float)):
                text = f"{number:g}%" if key in _PERCENT_STATS else f"{number:,.1f}".rstrip("0").rstrip(".")
            else:
                text = str(number)
            result[label] = text
        return result

    def _image(self, value: Any) -> str:
        text = str(value or "").strip()
        if not text or text.startswith(("http://", "https://", ":/")):
            return text
        root = self.data_dir.resolve()
        path = (root / text).resolve()
        return str(path) if root in path.parents else ""

    @staticmethod
    def _buffs(value: Any) -> tuple[tuple[str, float], ...]:
        buffs: list[tuple[str, float]] = []
        for item in value or []:
            if isinstance(item, dict):
                name, amount = item.get("name"), item.get("value", 0.0)
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                name, amount = item
            else:
                continue
            if isinstance(name, str) and name.strip() and isinstance(amount, (int, float)):
                buffs.append((name, float(amount)))
        return tuple(buffs)

    @staticmethod
    def _skills(raw_skills: dict[str, dict], language: str) -> tuple[Skill, ...]:
        skills: list[Skill] = []
        for key, raw in raw_skills.items():
            data = resolve(raw, language)
            name = str(data.get("name") or "").strip()
            description = str(data.get("description") or "").strip()
            if not name and not description:
                continue  # habilidade ainda não preenchida
            if not name and key in SKILL_LABELS:
                name = pick_text(SKILL_LABELS[key], language)
            skills.append(Skill(key, name, description))
        return tuple(skills)

    @staticmethod
    def _legacy_skills(kit: dict[str, Any]) -> tuple[Skill, ...]:
        return tuple(
            Skill("", str(item.get("name", "")), str(item.get("description", "")))
            for item in kit.get("skills", []) or []
            if isinstance(item, dict)
        )

    # ---------------------------------------------------------- integridade
    def check_integrity(self) -> IntegrityReport:
        errors: list[str] = []
        warnings: list[str] = []
        root = self.data_dir / "characters"
        if not root.is_dir():
            return IntegrityReport([f"pasta não existe: {root}"], [])

        for path in sorted(root.rglob("*.json")):
            relative = path.relative_to(self.data_dir).as_posix()
            if path.stat().st_size == 0:
                warnings.append(f"{relative}: arquivo vazio (use {{}} ou [])")
            elif path.stat().st_size > MAX_FILE_BYTES:
                errors.append(f"{relative}: maior que {MAX_FILE_BYTES // 1024} KB")
            else:
                try:
                    json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError) as error:
                    errors.append(f"{relative}: JSON inválido ({error})")

        known = {i.replace(" ", "_") for i in self.legacy.known_ids()}
        for folder in sorted((root / "data").glob("*")) if (root / "data").is_dir() else []:
            name = folder.name
            sheet = self._read(f"characters/data/{name}/{name}.json")
            if not isinstance(sheet, dict):
                continue
            if sheet.get("id") != name:
                errors.append(f"characters/data/{name}: campo id={sheet.get('id')!r} difere da pasta")
            if known and name not in known:
                warnings.append(f"characters/data/{name}: id fora de KNOWN_CHARACTER_IDS")
            if name == "rover":
                variants = [v for v in (root / "skills" / "rover").glob("*") if v.is_dir()]
                if not variants:
                    errors.append("rover: nenhuma pasta de variante em skills/rover/")
                continue
            for key, ref in (sheet.get("skills") or {}).items():
                safe = _safe_ref(ref)
                if not safe or not (self.data_dir / f"characters/skills/{safe}.json").is_file():
                    errors.append(f"characters/data/{name}: habilidade {key} -> {ref} não existe")
            sheet_raw, skills = self.raw_character(name)
            for key, data in skills.items():
                warnings.extend(self._translation_gaps(f"{name}/{key}", data))
            warnings.extend(self._translation_gaps(name, sheet_raw))

        if known:
            present = {p.name for p in (root / "data").glob("*")}
            for missing in sorted(known - present):
                if missing.startswith("rover_") and "rover" in present:
                    continue  # variantes do Rover vivem em skills/rover/<elemento>
                warnings.append(f"id do app sem pasta em characters/data: {missing}")
        return IntegrityReport(errors, warnings)

    def _translation_gaps(self, where: str, value: Any, path: str = "") -> Iterable[str]:
        if is_localized(value):
            have = {normalize_language(k) for k, v in value.items() if isinstance(v, str) and v.strip()}
            if have and have != set(LANGUAGES):
                missing = ", ".join(sorted(set(LANGUAGES) - have))
                yield f"{where}: {path or 'texto'} sem tradução ({missing})"
        elif isinstance(value, dict):
            for key, item in value.items():
                yield from self._translation_gaps(where, item, f"{path}.{key}".strip("."))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                yield from self._translation_gaps(where, item, f"{path}[{index}]")


# --------------------------------------------------- instância e atalhos
_default: Catalog | None = None


def default_catalog() -> Catalog:
    global _default
    if _default is None:
        _default = Catalog()
    return _default


def character(character_id: str, language: str = "PT-BR") -> Character:
    return default_catalog().character(character_id, language)
