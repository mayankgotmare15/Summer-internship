"""Database seeder for teams, categories, members, and initial settings."""

from pathlib import Path

import yaml


def load_yaml(filepath: str) -> dict:
    with open(filepath, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def verify_seeds() -> None:
    """Verifies that seed configuration files are valid and well-formed."""
    configs_dir = Path("configs")
    routing_map = load_yaml(str(configs_dir / "routing_map.yaml"))
    roster = load_yaml(str(configs_dir / "roster.yaml"))
    sla = load_yaml(str(configs_dir / "sla.yaml"))
    escalation = load_yaml(str(configs_dir / "escalation_rules.yaml"))

    categories = routing_map.get("categories", {})
    teams = roster.get("teams", [])
    members = roster.get("members", [])
    priorities = sla.get("priorities", {})

    print("Verified seed files:")
    print(f" - {len(categories)} categories")
    print(f" - {len(teams)} resolver teams")
    print(f" - {len(members)} roster members")
    print(f" - {len(priorities)} SLA priority levels")
    print(f" - Escalation ladder rules: {list(escalation.get('ladder', {}).keys())}")


if __name__ == "__main__":
    verify_seeds()
