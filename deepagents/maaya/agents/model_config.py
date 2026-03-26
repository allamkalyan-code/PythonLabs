"""Model tier resolution for Maaya v2.

Tiers:
  fast      — haiku-4-5  (cheap, quick tasks: spec-eval, database, devops, tester)
  balanced  — sonnet-4-6 (main orchestrator, planner, architect, frontend, backend)
  powerful  — opus-4-6   (override for highest-complexity tasks)
"""

import logging

logger = logging.getLogger(__name__)

# Tier → Anthropic model ID
_TIER_MODELS: dict[str, str] = {
    "fast": "anthropic:claude-haiku-4-5-20251001",
    "balanced": "anthropic:claude-sonnet-4-6",
    "powerful": "anthropic:claude-opus-4-6",
}

# Tier → max output tokens
MAX_OUTPUT_TOKENS: dict[str, int] = {
    "fast": 4096,
    "balanced": 8192,
    "powerful": 16384,
}

# Default when no tier is specified
DEFAULT_ORCHESTRATOR_MODEL = "anthropic:claude-sonnet-4-6"
DEFAULT_ORCHESTRATOR_TOKENS = MAX_OUTPUT_TOKENS["balanced"]


def get_model(tier: str) -> str:
    """Return the model ID for a given tier name.

    Args:
        tier: One of 'fast', 'balanced', 'powerful'.

    Returns:
        Full model string (e.g. 'anthropic:claude-sonnet-4-6').

    Raises:
        ValueError: If the tier name is not recognized.
    """
    if tier not in _TIER_MODELS:
        raise ValueError(f"Unknown model tier '{tier}'. Valid tiers: {list(_TIER_MODELS)}")
    return _TIER_MODELS[tier]


def get_max_tokens(tier: str) -> int:
    """Return the max output tokens for a given tier.

    Args:
        tier: One of 'fast', 'balanced', 'powerful'.

    Returns:
        Max output token count for the tier.
    """
    return MAX_OUTPUT_TOKENS.get(tier, MAX_OUTPUT_TOKENS["balanced"])
