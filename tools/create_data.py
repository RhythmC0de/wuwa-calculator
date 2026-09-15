from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "wuwa_calculator" / "data"


CHARACTER_SKILLS = (
    "basic_attack",
    "resonance_skill",
    "resonance_liberation",
    "forte_circuit",
    "intro_skill",
    "outro_skill",
)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    print(f"Created: {path.relative_to(ROOT)}")


def create_character(character_id: str) -> None:
    character_dir = DATA / "characters"

    data_dir = character_dir / "data" / character_id
    skills_dir = character_dir / "skills" / character_id
    icons_dir = character_dir / "icons"

    data_dir.mkdir(parents=True, exist_ok=True)
    skills_dir.mkdir(parents=True, exist_ok=True)
    icons_dir.mkdir(parents=True, exist_ok=True)

    character = {
        "id": character_id,
        "name": "",
        "rarity": None,
        "category": None,
        "element": None,
        "weapon_type": None,
        "base_stats": {},
        "skills": {
            skill: f"{character_id}/{skill}"
            for skill in CHARACTER_SKILLS
        },
    }

    write_json(
        data_dir / f"{character_id}.json",
        character,
    )

    for skill in CHARACTER_SKILLS:
        skill_data = {
            "id": f"{character_id}_{skill}",
            "name": "",
            "description": "",
            "effects": [],
            "scalings": [],
        }

        write_json(
            skills_dir / f"{skill}.json",
            skill_data,
        )

    print(f"\nCharacter '{character_id}' created successfully.")


def main() -> None:
    if len(sys.argv) != 3:
        print("Usage:")
        print("  python tools/create_data.py character <character_id>")
        sys.exit(1)

    data_type = sys.argv[1]
    identifier = sys.argv[2].lower()

    if data_type == "character":
        create_character(identifier)
    else:
        print(f"Unknown data type: {data_type}")
        sys.exit(1)


if __name__ == "__main__":
    main()