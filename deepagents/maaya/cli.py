"""Maaya CLI — skills marketplace and utility commands.

Usage:
    maaya skill list                  List all available skills from the registry
    maaya skill list --installed      List only locally installed skills
    maaya skill add <name>            Download and install a skill
    maaya skill remove <name>         Remove an installed skill
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

MAAYA_DIR = Path(__file__).parent
SKILLS_DIR = MAAYA_DIR / "skills"
REGISTRY_FILE = MAAYA_DIR / "registry.json"


def _load_registry() -> list[dict]:
    if not REGISTRY_FILE.exists():
        print("Error: registry.json not found.", file=sys.stderr)
        sys.exit(1)
    with open(REGISTRY_FILE) as f:
        return json.load(f)


def _installed_skills() -> set[str]:
    if not SKILLS_DIR.exists():
        return set()
    return {d.name for d in SKILLS_DIR.iterdir() if (d / "SKILL.md").exists()}


def cmd_skill_list(args: argparse.Namespace) -> None:
    registry = _load_registry()
    installed = _installed_skills()

    if args.installed:
        entries = [r for r in registry if r["name"] in installed]
        if not entries:
            unlisted = installed - {r["name"] for r in registry}
            all_installed = sorted(installed)
            if all_installed:
                print("Installed skills (not in registry):")
                for name in all_installed:
                    print(f"  {name}")
            else:
                print("No skills installed.")
            return
    else:
        entries = registry

    col = max(len(r["name"]) for r in entries) + 2
    for r in entries:
        marker = " ✓" if r["name"] in installed else "  "
        print(f"{marker} {r['name']:<{col}} {r['description']}")

    if not args.installed:
        n_installed = len(installed & {r["name"] for r in registry})
        print(f"\n{n_installed}/{len(registry)} installed. Use 'maaya skill add <name>' to install.")


def cmd_skill_add(args: argparse.Namespace) -> None:
    name = args.name
    registry = _load_registry()
    entry = next((r for r in registry if r["name"] == name), None)

    if entry is None:
        print(f"Error: '{name}' not found in registry. Run 'maaya skill list' to see available skills.")
        sys.exit(1)

    skill_dir = SKILLS_DIR / name
    skill_md = skill_dir / "SKILL.md"

    if skill_md.exists():
        print(f"'{name}' is already installed. Use 'maaya skill remove {name}' first to reinstall.")
        sys.exit(0)

    print(f"Downloading {name}...")
    try:
        with urlopen(entry["url"], timeout=10) as resp:
            content = resp.read().decode("utf-8")
    except URLError as e:
        print(f"Error: could not download skill — {e}")
        print("Note: Registry URLs are placeholders. Contribute skills at https://github.com/maaya-skills/registry")
        sys.exit(1)

    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md.write_text(content, encoding="utf-8")
    print(f"Installed '{name}' → {skill_md}")
    print("Restart the Maaya server for the skill to take effect.")


def cmd_skill_remove(args: argparse.Namespace) -> None:
    name = args.name
    skill_dir = SKILLS_DIR / name

    if not (skill_dir / "SKILL.md").exists():
        print(f"'{name}' is not installed.")
        sys.exit(1)

    import shutil
    shutil.rmtree(skill_dir)
    print(f"Removed '{name}'.")
    print("Restart the Maaya server for the change to take effect.")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="maaya",
        description="Maaya CLI — manage skills and configuration.",
    )
    subparsers = parser.add_subparsers(dest="command")

    # maaya skill ...
    skill_parser = subparsers.add_parser("skill", help="Manage Maaya skills")
    skill_sub = skill_parser.add_subparsers(dest="skill_command")

    list_p = skill_sub.add_parser("list", help="List available skills")
    list_p.add_argument("--installed", action="store_true", help="Show only installed skills")

    add_p = skill_sub.add_parser("add", help="Install a skill from the registry")
    add_p.add_argument("name", help="Skill name (see 'maaya skill list')")

    remove_p = skill_sub.add_parser("remove", help="Remove an installed skill")
    remove_p.add_argument("name", help="Skill name to remove")

    args = parser.parse_args()

    if args.command == "skill":
        if args.skill_command == "list":
            cmd_skill_list(args)
        elif args.skill_command == "add":
            cmd_skill_add(args)
        elif args.skill_command == "remove":
            cmd_skill_remove(args)
        else:
            skill_parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
